import logging
import requests
from typing import Dict, Optional, Literal
import json
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Provider type
ProviderType = Literal["ollama", "openrouter", "openai", "groq", "cloud"]


# Simplified prompt for LLM (after NER preprocessing)
LLM_FINALIZATION_PROMPT = """РОЛЬ: Ты — эксперт по **художественной анонимизации** юридических документов на русском и казахском языках. Твоя задача — заменить все конфиденциальные данные **вымышленными, но реалистичными** аналогами.

ВАЖНО: ТЕКСТ УЖЕ ПРЕДВАРИТЕЛЬНО ОЧИЩЕН NER-системой. Большинство ФИО, номеров и адресов уже заменены на плейсхолдеры ([ЛИЦО-1], [ОРГ-1], [ТЕЛЕФОН], [EMAIL] и т.д.).

ТВОЯ ЗАДАЧА:
1. **Заменить ВСЕ плейсхолдеры** ([ЛИЦО-X], [ОРГ-X], [ГЕО-X], [АДРЕС-X] и т.д.) на **вымышленные сущности**.
2. Найти и заменить ОСТАВШИЕСЯ (пропущенные NER) конфиденциальные данные, также используя вымышленные аналоги.
3. Обеспечить юридическую и лингвистическую целостность текста.
4. Исправить разорванные слова.

ПРАВИЛА ЗАМЕНЫ НА ВЫМЫШЛЕННЫЕ ДАННЫЕ:

1. ЛИЦА (РУ/КЗ):
   * Заменяй **[ЛИЦО-X]** на **полное вымышленное ФИО** (например, Иван Смирнов, Қайрат Асқарұлы).
   * Если требуется только фамилия, используй только вымышленную фамилию (Смирнов, Асқарұлы).
   * **Сохраняй национальную принадлежность:** Русские имена заменяй на русские, казахские – на казахские.
   * **Последовательность:** Одно и то же [ЛИЦО-X] должно быть заменено на одно и то же вымышленное ФИО по всему документу.

2. ОРГАНИЗАЦИИ (РУ/КЗ):
   * Заменяй **[ОРГ-X]** на **вымышленное, но правдоподобное** название (например, "Общество с ограниченной ответственностью 'Альфа-Плюс'", "ЖШС 'Көкжиек Консалтинг'").
   * Сохраняй тип организации (Суд $\rightarrow$ Вымышленный Суд, Полиция $\rightarrow$ Вымышленный Отдел Полиции).

3. ГЕОГРАФИЯ И АДРЕСА (РУ/КЗ):
   * Заменяй **[ГЕО-X]** на **вымышленный город/область** (например, "город Заречный", "Отырар облысы").
   * Заменяй **[АДРЕС-X]** на **полный вымышленный адрес** (например, "улица Мирная, дом 15, квартира 4", "Әл-Фараби даңғылы, 8-үй").

4. ДРУГИЕ ДАННЫЕ:
   * **[ТЕЛЕФОН], [EMAIL], [НОМЕР_ДЕЛА] и т.д.:** Заменяй на **правдоподобные вымышленные аналоги** (например, +7-707-123-45-67, a.smirnov@fakecorp.kz, ДЕЛО №456/2025).

5. Инициалы в подписи (/А.А./) → Используй инициалы вымышленного лица.

НЕ ИЗМЕНЯТЬ:
* Юридическая терминология (статья 175, Қылмыстық кодекс, УК РК и т.д.)
* Структура документа, абзацы, нумерация.
* Общие должности без имен (прокурор, тергеуші, судья).
* Временные рамки и сроки процедур.
* **ДАТЫ:** Если [ДАТА_РОЖДЕНИЯ], заменяй на вымышленную дату. Остальные даты (событий) сохраняй, если они важны для хронологии.

ОБЯЗАТЕЛЬНО:
* Склеивай разорванные слова: «заңб ұзушылық» → «заңбұзушылық», «қай та» → «қайта».
* Сохраняй оба языка, если документ двуязычный.
* НЕ переводи текст с одного языка на другой.
* Проверь грамматическую целостность казахского и русского.

ФОРМАТ ОТВЕТА: Верни ТОЛЬКО очищенный и заполненный вымышленными данными текст без комментариев.

ТЕКСТ:

{text}"""

# Full prompt for direct LLM cleaning (without NER - legacy support)
CLEANING_PROMPT = """Ты — эксперт по анонимизации юридических документов на русском и казахском языках. Твоя задача — полностью очистить предоставленный текст от всех персональных и конфиденциальных данных, сохранив структуру, смысл и юридическую терминологию документа.

ВАЖНО: Документ может быть на русском языке, казахском языке, или содержать оба языка. Обрабатывай персональные данные на обоих языках одинаково.

ПРАВИЛА ЗАМЕНЫ:

1. ЛИЧНЫЕ ДАННЫЕ (РУССКИЙ И КАЗАХСКИЙ):
   РУССКИЕ ИМЕНА:
   - ФИО полностью (Иванов Иван Иванович) → "Гражданин А."
   - Только фамилия (Иванов) → "Гражданин Б."
   - Имя и отчество без фамилии → "Гражданин В."
   - Инициалы (И.И. Иванов, Иванов И.И.) → "Гражданин Г."
   - Должности с именами (капитан Иванов, лейтенант Петров) → "Капитан Д.", "Лейтенант Е."

   КАЗАХСКИЕ ИМЕНА:
   - ФИО полностью (Нұрболат Әлі Серікұлы) → "Азамат А."
   - Только фамилия/имя (Нұрболат, Серікұлы) → "Азамат Б."
   - С указанием должности (капитан Әлі, аға лейтенант Серік) → "Капитан В.", "Аға лейтенант Г."
   - Инициалы (Н.Ә. Серікұлы) → "Азамат Д."
   - Казахские отчества (улы, қызы) → заменять вместе с ФИО

   ДВУЯЗЫЧНЫЕ ФОРМЫ:
   - Если имя указано на двух языках (Иванов/Иванов, Нұрболат/Нурболат) → заменять оба варианта на один плейсхолдер
   - Используй последовательные буквы русского алфавита (А., Б., В., Г., Д., Е., Ж., З. и т.д.)

2. ДОЛЖНОСТИ И ЗВАНИЯ (РУССКИЙ И КАЗАХСКИЙ):
   РУССКИЙ:
   - "Начальник отдела полиции Иванов" → "Начальник отдела полиции Ж."
   - "Прокурор Петров" → "Прокурор З."
   - "Дежурный офицер Сидоров" → "Дежурный офицер И."

   КАЗАХСКИЙ:
   - "Полиция бөлімінің бастығы Нұрболат" → "Полиция бөлімінің бастығы К."
   - "Прокурор Әлі" → "Прокурор Л."
   - "Кезекші офицер Серік" → "Кезекші офицер М."

3. ОРГАНИЗАЦИИ (РУССКИЙ И КАЗАХСКИЙ):
   РУССКИЙ:
   - Конкретные названия (МВД РФ по городу Москва) → "Организация А."
   - Отделения полиции (ОМВД России по району Х) → "Организация Б."
   - Суды (Московский районный суд) → "Организация В."
   - Частные компании → "Организация Г.", "Организация Д." и т.д.

   КАЗАХСКИЙ:
   - Конкретные названия (Алматы қаласы ІІМ) → "Ұйым А." или "Организация А."
   - Отделения полиции (Қарасай ауданы ІІБ) → "Ұйым Б." или "Организация Б."
   - Суды (Алматы қалалық соты) → "Ұйым В." или "Организация В."
   - Частные компании → "Ұйым Г.", "Ұйым Д." или использовать "Организация..."

   ВАЖНО: Для организаций можешь использовать русские плейсхолдеры "Организация А." даже если текст на казахском

4. ГЕОГРАФИЧЕСКИЕ ДАННЫЕ (РУССКИЙ И КАЗАХСКИЙ):
   РУССКИЙ:
   - Точные адреса (ул. Ленина, д. 5, кв. 10) → "адрес №1"
   - Города (если не критичны для понимания) → "город А."
   - Регионы → "регион Б."
   - Конкретные места преступлений → "место происшествия №1"

   КАЗАХСКИЙ:
   - Точные адреса (Абай көшесі, 5-үй, 10-пәтер) → "мекенжай №1" или "адрес №1"
   - Города (Алматы, Астана, Шымкент) → "қала А." или "город А."
   - Регионы (Алматы облысы) → "облыс Б." или "регион Б."
   - Места происшествий (оқиға орны) → "оқиға орны №1" или "место происшествия №1"

   ВАЖНО: Можешь использовать русские плейсхолдеры даже для казахских географических названий

5. КОНТАКТНЫЕ ДАННЫЕ:
   - Телефоны (+7-XXX-XXX-XX-XX) → "[ТЕЛЕФОН]"
   - Email (ivanov@example.com) → "[EMAIL]"

6. ДОКУМЕНТЫ И НОМЕРА (РУССКИЙ И КАЗАХСКИЙ):
   - Серии и номера паспортов → "[ПАСПОРТ]" или "[ТӨЛҚҰЖАТ]"
   - СНИЛС → "[СНИЛС]"
   - ИНН / ИИН / ЖСН (Жеке Сәйкестендіру Нөмірі) → "[ИНН]" или "[ЖСН]"
   - БИН (Бизнес Идентификационный Номер) → "[БИН]"
   - Номера дел → "[ДЕЛО №XXX]" или "[ІС №XXX]"
   - Номера постановлений → "[ПОСТАНОВЛЕНИЕ №XXX]" или "[ҚАУЛЫ №XXX]"
   - Удостоверения (куәлік) → "[УДОСТОВЕРЕНИЕ]" или "[КУӘЛІК]"

7. ДАТЫ:
   - Даты рождения → "[ДАТА РОЖДЕНИЯ]"
   - Конкретные даты событий можно сохранить, если они важны для хронологии (например, "15 января 2024 года")

8. СПЕЦИФИЧЕСКИЕ ДЕТАЛИ:
   - Номера автомобилей → "[ГОСНОМЕР]"
   - Банковские счета → "[СЧЕТ]"
   - Номера кредитных карт → "[КАРТА]"

ВАЖНО:
- НЕ изменяй юридическую терминологию и формулировки (на русском И на казахском языках)
- Сохраняй структуру документа (абзацы, списки, нумерацию)
- Сохраняй ссылки на законы, статьи, нормативные акты БЕЗ ИЗМЕНЕНИЙ на обоих языках
  Примеры: "Уголовный кодекс РК", "Қылмыстық кодекс", "статья 175", "175-бап"
- Сохраняй общие должности без привязки к конкретным лицам:
  Русский: "прокурор", "следователь", "судья", "дежурный"
  Казахский: "прокурор", "тергеуші", "судья", "кезекші"
- Сохраняй временные рамки и сроки на обоих языках
- Будь последовательным: одно и то же лицо должно заменяться на одну и ту же букву в пределах документа
- Если документ двуязычный, сохраняй оба языка после замены персональных данных
- Если сомневаешься, лучше заменить данные, чем оставить их
- НЕ переводи документ с одного языка на другой, сохраняй язык оригинала
- Исправление разрывов слов: После замены проверяй и склеивай разорванные казахские/русские слова (например, «заңб ұзушылық» → «заңбұзушылық», «қай та» → «қайта»). Сохраняй дефисы только в составных словах.
- Обработка организаций: Все конкретные названия компаний/учреждений (даже с датами вроде "-2020") заменяй на "Организация А.", "Ұйым А." последовательно в документе.
- Подпись в конце: Инициалы в подписи («/А.М./») → «/А.А./» или "[ПОДПИСЬ]".
- Валидация текста: Финальный шаг — проверка на грамматическую/орфографическую целостность казахского и русского без изменения смысла.

ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО очищенный текст без каких-либо комментариев, пояснений или дополнительного форматирования. Просто замени данные и верни результат.

ТЕКСТ ДЛЯ ОЧИСТКИ:

{text}"""


def clean_text_with_ollama(
    text: str,
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3",
    temperature: float = 0.1
) -> Dict[str, any]:
    """
    Clean personal data from text using Ollama LLM.

    Args:
        text: The text to clean
        ollama_url: URL of the Ollama server
        model: Name of the Ollama model to use
        temperature: Temperature for generation (lower = more deterministic)

    Returns:
        Dict containing:
            - cleaned_text: Text with personal data removed/masked
            - original_length: Length of original text
            - cleaned_length: Length of cleaned text
            - llm_model: Name of the model used
            - success: Whether the operation was successful
    """
    try:
        logger.info(f"Starting text cleaning with Ollama model: {model}")
        logger.info(f"Original text length: {len(text)} characters")

        # Prepare the prompt
        prompt = CLEANING_PROMPT.format(text=text)

        # Prepare the request to Ollama
        url = f"{ollama_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": -1  # No limit on output length
            }
        }

        logger.info(f"Sending request to Ollama at {url}")

        # Send request to Ollama
        response = requests.post(url, json=payload, timeout=300)  # 5 minute timeout
        response.raise_for_status()

        # Parse response
        result = response.json()
        cleaned_text = result.get("response", "")

        if not cleaned_text:
            raise ValueError("Ollama returned empty response")

        logger.info(f"Cleaned text length: {len(cleaned_text)} characters")
        logger.info(f"Cleaning completed successfully")

        return {
            "cleaned_text": cleaned_text.strip(),
            "original_length": len(text),
            "cleaned_length": len(cleaned_text.strip()),
            "llm_model": model,
            "success": True,
            "error": None
        }

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Failed to connect to Ollama at {ollama_url}. Is Ollama running?"
        logger.error(f"{error_msg}: {str(e)}")
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg
        }

    except requests.exceptions.Timeout as e:
        error_msg = "Request to Ollama timed out. Try with a shorter text or increase timeout."
        logger.error(f"{error_msg}: {str(e)}")
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg
        }

    except Exception as e:
        error_msg = f"Error during text cleaning: {str(e)}"
        logger.error(error_msg)
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg
        }


def test_ollama_connection(
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3"
) -> Dict[str, any]:
    """
    Test connection to Ollama and check if the model is available.

    Args:
        ollama_url: URL of the Ollama server
        model: Name of the model to check

    Returns:
        Dict with connection status and available models
    """
    try:
        # Test if Ollama is running
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        response.raise_for_status()

        models_data = response.json()
        available_models = [m.get("name", "") for m in models_data.get("models", [])]

        model_available = any(model in m for m in available_models)

        logger.info(f"Ollama connection successful. Available models: {available_models}")

        return {
            "connected": True,
            "available_models": available_models,
            "model_available": model_available,
            "requested_model": model,
            "error": None
        }

    except Exception as e:
        error_msg = f"Failed to connect to Ollama: {str(e)}"
        logger.error(error_msg)
        return {
            "connected": False,
            "available_models": [],
            "model_available": False,
            "requested_model": model,
            "error": error_msg
        }


def chunk_text(text: str, max_chunk_size: int = 8000) -> list[str]:
    """
    Split text into chunks for processing long documents.

    Args:
        text: Text to split
        max_chunk_size: Maximum size of each chunk in characters

    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    logger.info(f"Text split into {len(chunks)} chunks")
    return chunks


def clean_large_text_with_ollama(
    text: str,
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3",
    temperature: float = 0.1,
    max_chunk_size: int = 8000
) -> Dict[str, any]:
    """
    Clean large text by processing it in chunks.

    Args:
        text: The text to clean
        ollama_url: URL of the Ollama server
        model: Name of the Ollama model to use
        temperature: Temperature for generation
        max_chunk_size: Maximum size of each chunk

    Returns:
        Dict with cleaned text and metadata
    """
    try:
        # Split text into chunks
        chunks = chunk_text(text, max_chunk_size)

        if len(chunks) == 1:
            # Process single chunk
            return clean_text_with_ollama(text, ollama_url, model, temperature)

        # Process multiple chunks
        logger.info(f"Processing {len(chunks)} chunks")
        cleaned_chunks = []
        total_original_length = 0
        total_cleaned_length = 0

        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}")
            result = clean_text_with_ollama(chunk, ollama_url, model, temperature)

            if not result["success"]:
                return result

            cleaned_chunks.append(result["cleaned_text"])
            total_original_length += result["original_length"]
            total_cleaned_length += result["cleaned_length"]

        # Combine cleaned chunks
        cleaned_text = "\n\n".join(cleaned_chunks)

        logger.info(f"All chunks processed successfully")

        return {
            "cleaned_text": cleaned_text,
            "original_length": total_original_length,
            "cleaned_length": total_cleaned_length,
            "llm_model": model,
            "success": True,
            "error": None,
            "chunks_processed": len(chunks)
        }

    except Exception as e:
        error_msg = f"Error processing large text: {str(e)}"
        logger.error(error_msg)
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg
        }


# ============================================================================
# UNIVERSAL LLM FUNCTIONS (Supports both Ollama and Cloud providers)
# ============================================================================

def clean_text_with_llm(
    text: str,
    provider: ProviderType = "ollama",
    model: str = "llama3",
    temperature: float = 0.1,
    ollama_url: str = "http://localhost:11434",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, any]:
    """
    Universal function to clean text with LLM (supports Ollama and cloud providers).

    Args:
        text: The text to clean
        provider: LLM provider ('ollama', 'openrouter', 'openai', 'groq', 'cloud')
        model: Name of the model to use
        temperature: Temperature for generation
        ollama_url: URL for Ollama (if provider is 'ollama')
        base_url: Base URL for cloud providers
        api_key: API key for cloud providers

    Returns:
        Dict with cleaned text and metadata
    """
    from app.services.llm_service_cloud import clean_text_with_cloud_llm

    logger.info(f"Using LLM provider: {provider}")

    if provider == "ollama":
        # Use local Ollama
        if len(text) > 8000:
            return clean_large_text_with_ollama(text, ollama_url, model, temperature)
        else:
            return clean_text_with_ollama(text, ollama_url, model, temperature)
    else:
        # Use cloud provider (openrouter, openai, groq, etc.)
        if not base_url or not api_key:
            return {
                "cleaned_text": None,
                "original_length": len(text),
                "cleaned_length": 0,
                "llm_model": model,
                "success": False,
                "error": "base_url and api_key are required for cloud providers"
            }

        if len(text) > 12000:
            from app.services.llm_service_cloud import clean_large_text_with_cloud_llm
            return clean_large_text_with_cloud_llm(
                text, CLEANING_PROMPT, base_url, api_key, model, temperature
            )
        else:
            return clean_text_with_cloud_llm(
                text, CLEANING_PROMPT, base_url, api_key, model, temperature
            )


def test_llm_connection(
    provider: ProviderType = "ollama",
    model: str = "llama3",
    ollama_url: str = "http://localhost:11434",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, any]:
    """
    Test connection to LLM service (Ollama or cloud).

    Args:
        provider: LLM provider
        model: Model name
        ollama_url: Ollama URL (for local)
        base_url: Base URL (for cloud)
        api_key: API key (for cloud)

    Returns:
        Dict with connection status
    """
    from app.services.llm_service_cloud import test_cloud_llm_connection

    if provider == "ollama":
        return test_ollama_connection(ollama_url, model)
    else:
        if not base_url or not api_key:
            return {
                "connected": False,
                "model_available": False,
                "requested_model": model,
                "error": "base_url and api_key are required for cloud providers"
            }
        return test_cloud_llm_connection(base_url, api_key, model)


# ============================================================================
# RE-EXPORT OPENAI FUNCTIONS (for backwards compatibility)
# ============================================================================
from app.services.openai_functions import (
    generate_summary,
    generate_test,
    extract_text_from_file,
    _parse_situational_tests
)

def clean_text_with_ner_and_llm(
    text: str,
    provider: ProviderType = "ollama",
    model: str = "llama3",
    temperature: float = 0.1,
    ollama_url: str = "http://localhost:11434",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    use_ner: bool = True
) -> Dict[str, any]:
    """
    Two-stage pipeline: NER preprocessing + LLM finalization.

    This is the recommended approach for best quality.

    Args:
        text: Original text to clean
        provider: LLM provider
        model: Model name
        temperature: Temperature for LLM
        ollama_url: Ollama URL (for local)
        base_url: Base URL (for cloud)
        api_key: API key (for cloud)
        use_ner: Whether to use NER preprocessing (default: True)

    Returns:
        Dict with cleaned text, stats, and metadata
    """
    try:
        if use_ner:
            # Stage 1: NER Preprocessing
            logger.info("Stage 1: NER preprocessing...")
            from app.services.ner_service import preprocess_with_ner

            ner_result = preprocess_with_ner(text)

            if not ner_result["success"]:
                logger.warning(f"NER preprocessing failed: {ner_result['error']}")
                logger.info("Falling back to direct LLM cleaning...")
                preprocessed_text = text
                ner_stats = {}
            else:
                preprocessed_text = ner_result["preprocessed_text"]
                ner_stats = ner_result["stats"]
                logger.info(f"NER preprocessing complete. Replacements: {ner_stats['total_replacements']}")
        else:
            preprocessed_text = text
            ner_stats = {}

        # Stage 2: LLM Finalization
        logger.info("Stage 2: LLM finalization...")

        # Choose prompt based on whether NER was used
        prompt_template = LLM_FINALIZATION_PROMPT if use_ner else CLEANING_PROMPT

        # Use appropriate cleaning function
        from app.services.llm_service_cloud import clean_text_with_cloud_llm

        if provider == "ollama":
            # Use Ollama
            prompt = prompt_template.format(text=preprocessed_text)

            if len(preprocessed_text) > 8000:
                # For large texts, we need to handle chunking differently
                llm_result = clean_large_text_with_ollama(
                    preprocessed_text, ollama_url, model, temperature
                )
            else:
                llm_result = clean_text_with_ollama(
                    preprocessed_text, ollama_url, model, temperature
                )
        else:
            # Use cloud provider
            if not base_url or not api_key:
                return {
                    "cleaned_text": None,
                    "original_length": len(text),
                    "cleaned_length": 0,
                    "llm_model": model,
                    "success": False,
                    "error": "base_url and api_key are required for cloud providers",
                    "ner_stats": ner_stats
                }

            llm_result = clean_text_with_cloud_llm(
                preprocessed_text, prompt_template, base_url, api_key, model, temperature
            )

        if not llm_result["success"]:
            return {
                "cleaned_text": None,
                "original_length": len(text),
                "cleaned_length": 0,
                "llm_model": model,
                "success": False,
                "error": llm_result["error"],
                "ner_stats": ner_stats
            }

        # Combine results
        result = {
            "cleaned_text": llm_result["cleaned_text"],
            "original_text": text,
            "preprocessed_text": preprocessed_text if use_ner else None,
            "original_length": len(text),
            "cleaned_length": len(llm_result["cleaned_text"]),
            "llm_model": model,
            "success": True,
            "error": None,
            "ner_stats": ner_stats,
            "pipeline_used": "NER + LLM" if use_ner else "LLM Only"
        }

        logger.info(f"Two-stage cleaning complete. Original: {result['original_length']}, Final: {result['cleaned_length']}")
        if use_ner:
            logger.info(f"NER replaced {ner_stats.get('total_replacements', 0)} entities")

        return result

    except Exception as e:
        error_msg = f"Error in two-stage cleaning pipeline: {str(e)}"
        logger.error(error_msg)
        return {
            "cleaned_text": None,
            "original_length": len(text),
            "cleaned_length": 0,
            "llm_model": model,
            "success": False,
            "error": error_msg,
            "ner_stats": ner_stats if 'ner_stats' in locals() else {}
        }


__all__ = [
    'CLEANING_PROMPT',
    'LLM_FINALIZATION_PROMPT',
    'clean_text_with_ollama',
    'test_ollama_connection',
    'chunk_text',
    'clean_large_text_with_ollama',
    'clean_text_with_llm',
    'clean_text_with_ner_and_llm',
    'test_llm_connection',
    'generate_summary',
    'generate_test',
    'extract_text_from_file',
]

