"""
Service for generating case study questions using LLM.
This is separate from the test generation service to provide more detailed,
educational questions with comprehensive answers.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_case_questions(
    case_text: str,
    num_questions: int = 5,
    field_of_law: str = "уголовный процесс",
    target_audience: str = "студенты бакалавриата",
    jurisdiction: str = "Республика Казахстан, континентальная система",
    difficulty_level: str = "базовый"
) -> List[Dict[str, str]]:
    """
    Generate educational questions for a case study using LLM.

    This function creates detailed questions with comprehensive answers (300-700 words)
    suitable for legal education.

    Args:
        case_text: The case study text
        num_questions: Number of questions to generate (default: 5)
        field_of_law: Area of law (e.g., "уголовный процесс", "гражданское право")
        target_audience: Target audience (e.g., "студенты бакалавриата", "магистранты")
        jurisdiction: Legal jurisdiction (e.g., "Республика Казахстан")
        difficulty_level: Difficulty level ("базовый", "продвинутый", "экспертный")

    Returns:
        List of dicts with 'question' and 'answer' keys:
        [{
            "question": "Полный текст вопроса",
            "answer": "Развернутый ответ (300-700 слов)"
        }]
    """
    try:
        logger.info(f"Generating {num_questions} case questions")
        logger.info(f"Parameters: field={field_of_law}, audience={target_audience}, "
                   f"jurisdiction={jurisdiction}, difficulty={difficulty_level}")

        # Initialize OpenAI client
        client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY
        )

        # Prepare the prompt
        prompt = f"""
        !!! ПРИОРИТЕТНОЕ ТРЕБОВАНИЕ ЯЗЫКА ГЕНЕРАЦИИ !!!
        1. **Определи язык текста в КЕЙСОВОЙ ЗАДАЧЕ (\`case_text\`).**
        2. **Весь сгенерированный контент (вопросы, ответы, вводные и заключительные части) должен быть ТОЛЬКО на этом языке. Игнорируй язык, на котором написаны эти инструкции.**

        Ты — опытный методист-юрист по подготовке материалов для обучения студентов/слушателей
        юридических специальностей. Твоя задача — генерировать учебные вопросы к кейсовым
        задачам и разработанные ответы.

        ВХОДНЫЕ ДАННЫЕ:
        - Кейсовая задача (фабула, обстоятельства, участники, правовой контекст)
        - Количество вопросов: {num_questions}
        - Область права: {field_of_law}
        - Целевая аудитория: {target_audience}
        - Юрисдикция: {jurisdiction}
        - Уровень сложности: {difficulty_level}

        ТРЕБОВАНИЯ К ГЕНЕРАЦИИ ВОПРОСОВ:

        1. СТРУКТУРА КАЖДОГО ВОПРОСА:
           - Номер и формулировка вопроса (чёткая, однозначная)
           - Тип вопроса (один из вариантов):
             * Вопрос на применение норм права (требует ссылки на конкретные статьи закона)
             * Вопрос на анализ коллизии (требует разрешения противоречия)
             * Вопрос на оценку правомерности действия (требует критического анализа)
             * Вопрос на процессуальный алгоритм (требует описания последовательности)
             * Вопрос на принятие решения/подготовку документа (требует практического результата)

        2. РАЗНООБРАЗИЕ ВОПРОСОВ:
           - Минимум 1 вопрос — на знание нормативной базы
           - Минимум 1 вопрос — на выявление нарушений/коллизий
           - Минимум 1 вопрос — на процессуальный порядок
           - Минимум 1-2 вопроса — на составление документов или принятие решений
           - Баланс между теорией и практикой

        3. РАЗВЕРНУТЫЙ ОТВЕТ К КАЖДОМУ ВОПРОСУ:
           - Объём: 100-300 слов (достаточный для понимания, но не избыточный)
           - Структура ответа:
             * Вводная часть (определение ключевого понятия или постановка проблемы)
             * Основная часть (разбор с указанием нормативных ссылок и аргументов)
             * Заключительная часть (вывод или практическое рекомендация)
           - Цитирование закона: указывай точные номера статей, пункты, части
           - Методический подход: объясняй «почему» это так, а не только «что это»
           - Практическая значимость: указывай, как это применяется в реальных ситуациях

        4. МЕТОДИЧЕСКИЕ ТРЕБОВАНИЯ:
           - Вопросы должны быть прогрессивно сложны (от простого к сложному)
           - Каждый вопрос должен направлять студента к глубокому пониманию предмета
           - Ответы должны быть корректны с юридической точки зрения
           - Используй терминологию, соответствующую правовой системе {jurisdiction}
           - Избегай двусмысленности и неточности формулировок
           - Язык генерации: Используй тот же язык, на котором написана КЕЙСОВАЯ ЗАДАЧА (`case_text`).

        ФОРМАТ ВЫВОДА:
        Используй строго следующий формат для каждого вопроса (на языке \`case_text\`):

        ВОПРОС 1
        [Текст вопроса]

        ОТВЕТ 1
        [Развернутый ответ 100-300 слов]

        ---

        ВОПРОС 2
        [Текст вопроса]

        ОТВЕТ 2
        [Развернутый ответ 100-300 слов]

        ---

        (и так далее для всех {num_questions} вопросов)

        КЕЙСОВАЯ ЗАДАЧА:

        {case_text}"""

        logger.info("Sending request to LLM (openai/gpt-5.1)")

        # Send request to OpenAI API (via OpenRouter)
        response = client.chat.completions.create(
            model="openai/gpt-5.1",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — опытный методист-юрист, эксперт по разработке учебных материалов для юридического образования."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Низкая температура для более точных ответов
            max_tokens=16000  # Достаточно для развернутых ответов
        )

        response_text = response.choices[0].message.content

        if not response_text:
            logger.error("LLM returned empty response")
            raise ValueError("LLM returned empty response")

        logger.info(f"Received response from LLM, length: {len(response_text)} characters")

        # Parse the response
        questions = _parse_case_questions(response_text)

        if not questions:
            logger.error(f"Failed to parse questions from response: {response_text[:500]}")
            raise ValueError("Failed to parse questions from LLM response")

        logger.info(f"Successfully parsed {len(questions)} questions")

        return questions

    except Exception as e:
        logger.error(f"Error generating case questions: {str(e)}")
        raise Exception(f"Failed to generate case questions: {str(e)}")


def _parse_case_questions(response_text: str) -> List[Dict[str, str]]:
    """
    Parse case questions from LLM response.

    Expected format:
    ВОПРОС 1
    [question text]

    ОТВЕТ 1
    [answer text]

    ---

    ВОПРОС 2
    ...

    Args:
        response_text: Raw response from LLM

    Returns:
        List of dicts with 'question' and 'answer' keys
    """
    questions = []

    try:
        # Split by --- separator or by ВОПРОС pattern
        # First try splitting by ---
        blocks = re.split(r'\n---+\n', response_text.strip())

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Extract question and answer using regex
            # Pattern: ВОПРОС X \n [text] \n ОТВЕТ X \n [text]
            question_match = re.search(
                r'ВОПРОС\s+\d+\s*\n(.+?)\n\s*ОТВЕТ\s+\d+\s*\n(.+)',
                block,
                re.DOTALL | re.IGNORECASE
            )

            if question_match:
                question_text = question_match.group(1).strip()
                answer_text = question_match.group(2).strip()

                questions.append({
                    "question": question_text,
                    "answer": answer_text
                })
            else:
                logger.warning(f"Could not parse block: {block[:100]}")

        # If the above didn't work, try alternative parsing
        if not questions:
            logger.info("Trying alternative parsing method")
            # Split by ВОПРОС pattern
            parts = re.split(r'ВОПРОС\s+\d+', response_text, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip()]

            for part in parts:
                # Find ОТВЕТ in this part
                answer_match = re.search(r'ОТВЕТ\s+\d+\s*\n(.+)', part, re.DOTALL | re.IGNORECASE)
                if answer_match:
                    # Everything before ОТВЕТ is question
                    question_text = re.sub(r'ОТВЕТ\s+\d+.*', '', part, flags=re.DOTALL | re.IGNORECASE).strip()
                    answer_text = answer_match.group(1).strip()

                    if question_text and answer_text:
                        questions.append({
                            "question": question_text,
                            "answer": answer_text
                        })

        logger.info(f"Parsed {len(questions)} questions using regex")
        return questions

    except Exception as e:
        logger.error(f"Error parsing case questions: {str(e)}")
        return []
