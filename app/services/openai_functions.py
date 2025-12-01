"""
OpenAI API functions for generating summaries and tests.
These were originally in llm_service.py
"""
import logging
import re
from typing import List, Dict, Any
from openai import OpenAI
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def _parse_situational_tests(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse situational test format into JSON structure.

    Expected format:
    Ситуация 1
    [situation text]
    Вопрос: [question]
    Варианты ответов:
    A) option1
    B) option2
    C) option3
    D) option4
    Правильный ответ: [letter].
    """
    questions = []

    # Split by "Ситуация" and skip the first empty element
    situations = re.split(r'Ситуация \d+', response_text)
    situations = [s.strip() for s in situations if s.strip()]

    for situation_block in situations:
        try:
            # Extract question
            question_match = re.search(r'Вопрос:\s*(.+?)(?=Варианты ответов:)', situation_block, re.DOTALL)
            if not question_match:
                continue

            situation_text = situation_block[:question_match.start()].strip()
            question_text = question_match.group(1).strip()

            # Combine situation and question
            full_question = f"{situation_text}\n\n{question_text}"

            # Extract options
            options_match = re.search(r'Варианты ответов:\s*A\)\s*(.+?)\s*B\)\s*(.+?)\s*C\)\s*(.+?)\s*D\)\s*(.+?)(?=Правильный ответ:)',
                                     situation_block, re.DOTALL)
            if not options_match:
                continue

            options = [
                options_match.group(1).strip(),
                options_match.group(2).strip(),
                options_match.group(3).strip(),
                options_match.group(4).strip()
            ]

            # Extract correct answer letter
            correct_match = re.search(r'Правильный ответ:\s*([A-D])', situation_block)
            if not correct_match:
                continue

            correct_letter = correct_match.group(1)
            letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            correct_answer = options[letter_to_index[correct_letter]]

            questions.append({
                "question": full_question,
                "options": options,
                "correct_answer": correct_answer
            })

        except Exception as e:
            logger.error(f"Error parsing situation block: {str(e)}")
            continue

    return questions


def generate_summary(text: str = None, file_url: str = None, max_tokens: int = 1000) -> str:
    """
    Generate a summary from the given text or file using OpenAI API.

    Args:
        text: The original text to summarize (optional)
        file_url: URL to the file to summarize (optional)
        max_tokens: Maximum number of tokens in the response

    Returns:
        str: The generated summary

    Note: Either text or file_url must be provided
    """
    from app.core.config import settings

    if not text and not file_url:
        raise ValueError("Either text or file_url must be provided")

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Prompt for summarization
        prompt_text = """Создай краткий и структурированный конспект на русском языке из предоставленного материала.

Конспект должен быть:
- Кратким и информативным (примерно на 1 страницу)
- Хорошо структурированным с заголовками и подзаголовками
- Содержать ключевые моменты и важную информацию
- Написан простым и понятным языком"""

        # If file_url is provided, use responses API with file support
        if file_url:
            logger.info(f"Generating summary from file: {file_url}")

            response = client.responses.create(
                model="gpt-5",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt_text
                            },
                            {
                                "type": "input_file",
                                "file_url": file_url
                            }
                        ]
                    }
                ]
            )
            summary = response.output_text

        # If text is provided, use standard chat completion
        else:
            logger.info(f"Generating summary for text of length: {len(text)}")

            full_prompt = f"{prompt_text}\n\nТекст для конспектирования:\n{text}"

            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Ты - профессиональный методист, который создает качественные учебные материалы."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=max_tokens
            )
            summary = response.choices[0].message.content

        if not summary:
            logger.warning("Received empty summary from OpenAI API")
            return ""

        logger.info(f"Summary generated successfully. Length: {len(summary)}")
        logger.info(f"Summary content preview: {summary[:200]}...")
        return summary

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise Exception(f"Failed to generate summary: {str(e)}")


def generate_test(text: str = None, file_url: str = None, num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Generate multiple choice questions from the given text or file using OpenAI API.

    Args:
        text: The original text to generate questions from (optional)
        file_url: URL to the file to generate questions from (optional)
        num_questions: Number of questions to generate

    Returns:
        List[Dict]: List of questions in format:
            [{question, options: [list of answers], correct_answer: actual answer text}]

    Note: Either text or file_url must be provided
    """
    from app.core.config import settings

    if not text and not file_url:
        raise ValueError("Either text or file_url must be provided")

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Prompt for test generation
        prompt_text = """Ты — методист по оценочным материалам в юриспруденции и эксперт по нормоконтролю правоохранительных органов. Тебе передают текст прокурорского представления (далее — Документ). Задача: сгенерировать ровно 5 ситуационных тестов на основе содержания Документа. Каждый тест состоит из короткой ситуации, одного вопроса, четырёх вариантов ответов (A–D) и строки «Правильный ответ: [буква]». Объяснения и обоснования не предоставляй.

Требования к генерации:

Источник фактов и норм — только Документ: извлеки упомянутые нормы права, сроки, процессуальные действия, роли должностных лиц, требования прокурора и меры реагирования. Не добавляй нормы и темы, которых нет в Документе.

Ситуации должны варьироваться по ролям (например, дежурный офицер, участковый, следователь, руководитель подразделения, прокурор), процессуальным этапам, срокам, видам нарушений и управленческим мерам, но все они должны логично вытекать из Документа.

В каждом тесте задавай один чёткий вопрос в стиле: «Что нарушено?», «Какая норма применима?», «Какая мера правомерна?», «Кто обязан совершить действие по Документу?».

Варианты ответов: один корректный и три правдоподобных, но неверных по сути, норме или субъекту; избегай очевидных «пустых» дистракторов.

Персональные данные не раскрывай; используй нейтральные обозначения: «гражданин А.», «лейтенант Б.», «начальник отдела», «прокурор города».

Формат вывода строго как ниже, без дополнительных комментариев, пояснений, заголовков и пустых строк в конце.

Формат вывода (ровно для 5 кейсов):
Ситуация 1
[4–7 предложений, описывающих эпизод, в котором обыгрывается конкретная норма/требование из Документа.]
Вопрос: [1 предложение, чёткий вопрос по сути кейса.]
Варианты ответов:
A) …
B) …
C) …
D) …
Правильный ответ: [буква].

Ситуация 2
[текст ситуации]
Вопрос: …
Варианты ответов:
A) …
B) …
C) …
D) …
Правильный ответ: [буква].

Ситуация 3
[текст ситуации]
Вопрос: …
Варианты ответов:
A) …
B) …
C) …
D) …
Правильный ответ: [буква].

Ситуация 4
[текст ситуации]
Вопрос: …
Варианты ответов:
A) …
B) …
C) …
D) …
Правильный ответ: [буква].

Ситуация 5
[текст ситуации]
Вопрос: …
Варианты ответов:
A) …
B) …
C) …
D) …
Правильный ответ: [буква].

Правила качества:

Каждый тест опирается на конкретные фразы и требования из Документа: сроки, процедуры, обязанности, полномочия, контроль, виды мер реагирования; избегай тем, которых нет в Документе.

Корректный вариант должен точно соответствовать норме/требованию из Документа (указывай номер статьи или наименование акта только если оно явно присутствует во входном тексте).

Не добавляй объяснений, ссылок, цитат и правовых комментариев вне правильного ответа-буквы."""

        # If file_url is provided, use responses API with file support
        if file_url:
            logger.info(f"Generating {num_questions} test questions from file: {file_url}")

            response = client.responses.create(
                model="gpt-5",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt_text
                            },
                            {
                                "type": "input_file",
                                "file_url": file_url
                            }
                        ]
                    }
                ]
            )
            response_text = response.output_text

        # If text is provided, use standard chat completion
        else:
            logger.info(f"Generating {num_questions} test questions for text of length: {len(text)}")

            response = client.responses.create(
                model="gpt-5",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt_text
                            },
                            {
                                "type": "input_text",
                                "text": text
                            }
                        ]
                    }
                ]
            )
            response_text = response.output_text

        # Parse the text format response
        try:
            questions = _parse_situational_tests(response_text)

            # Validate the structure
            for q in questions:
                if not all(key in q for key in ["question", "options", "correct_answer"]):
                    raise ValueError("Invalid question structure")
                if len(q["options"]) != 4:
                    raise ValueError("Each question must have exactly 4 options")

            logger.info(f"Generated {len(questions)} test questions successfully")
            return questions

        except Exception as e:
            logger.error(f"Failed to parse test response: {response_text}")
            raise Exception(f"Failed to parse test questions: {str(e)}")

    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        raise Exception(f"Failed to generate test: {str(e)}")


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract text from various file formats.

    Args:
        file_path: Path to the file
        file_type: Type of file (txt, docx, pdf)

    Returns:
        str: Extracted text
    """
    try:
        if file_type == "txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        elif file_type == "docx":
            from docx import Document
            doc = Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif file_type == "pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        raise Exception(f"Failed to extract text: {str(e)}")
