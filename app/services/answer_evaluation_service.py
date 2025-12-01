"""
Service for evaluating student answers using LLM.
Compares student answer with correct answer and returns a score (0-100).
"""
import logging
import re
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


def evaluate_answer(
    student_answer: str,
    correct_answer: str,
    question: str
) -> int:
    """
    Evaluate student's answer using LLM and return a score from 0 to 100.

    Args:
        student_answer: The answer provided by the student
        correct_answer: The correct/reference answer from case_test
        question: The question text for context

    Returns:
        Integer score from 0 to 100
    """
    try:
        logger.info("Evaluating student answer using LLM")

        # Initialize OpenAI client
        client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY
        )

        # Prepare the evaluation prompt
        prompt = f"""Ты — опытный преподаватель юридических дисциплин, эксперт по оценке ответов студентов.

Твоя задача — оценить ответ студента на вопрос по юридическому кейсу и выставить оценку от 0 до 100 баллов.

КРИТЕРИИ ОЦЕНКИ:

1. ПРАВИЛЬНОСТЬ (40 баллов):
   - Правильно ли студент определил применимые нормы права?
   - Верно ли указаны статьи законов и их содержание?
   - Правильно ли сделаны юридические выводы?

2. ПОЛНОТА (30 баллов):
   - Охватывает ли ответ все ключевые аспекты вопроса?
   - Приведены ли все необходимые аргументы?
   - Раскрыты ли все важные детали?

3. ОБОСНОВАННОСТЬ (20 баллов):
   - Логична ли аргументация?
   - Приведены ли ссылки на нормативные акты?
   - Обоснованы ли выводы?

4. СТРУКТУРА И ЯСНОСТЬ (10 баллов):
   - Логична ли структура ответа?
   - Понятно ли изложение?
   - Соблюдена ли юридическая терминология?

ВОПРОС:
{question}

ЭТАЛОННЫЙ ОТВЕТ:
{correct_answer}

ОТВЕТ СТУДЕНТА:
{student_answer}

ИНСТРУКЦИЯ ПО ОЦЕНКЕ:

1. Сравни ответ студента с эталонным ответом.
2. Оцени по каждому из четырёх критериев.
3. Выведи ТОЛЬКО ОДНО ЦЕЛОЕ ЧИСЛО от 0 до 100 — итоговую оценку.
4. НЕ пиши объяснений, комментариев или других слов.
5. Ответ должен содержать ТОЛЬКО число (например: 85).

ТВОЙ ОТВЕТ (ТОЛЬКО ЧИСЛО):"""

        logger.info("Sending evaluation request to LLM (openai/gpt-5.1)")

        # Send request to OpenAI API (via OpenRouter)
        response = client.chat.completions.create(
            model="openai/gpt-5.1",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — опытный преподаватель юридических дисциплин. Оценивай ответы студентов объективно и справедливо. Выводи ТОЛЬКО число от 0 до 100."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Низкая температура для более консистентной оценки
            max_tokens=1000  # Достаточно для reasoning и ответа (GPT-5.1 использует reasoning mode)
        )

        logger.info(f"Full LLM response: {response}")

        response_text = response.choices[0].message.content

        if not response_text:
            logger.error(f"LLM returned empty response. Full response: {response.model_dump()}")
            raise ValueError("LLM returned empty response")

        response_text = response_text.strip()
        logger.info(f"Received response from LLM: {response_text}")

        # Extract score from response (should be just a number)
        score = _parse_score(response_text)

        logger.info(f"Parsed score: {score}")

        return score

    except Exception as e:
        logger.error(f"Error evaluating answer: {str(e)}")
        raise Exception(f"Failed to evaluate answer: {str(e)}")


def _parse_score(response_text: str) -> int:
    """
    Parse score from LLM response.
    Expects a number from 0 to 100.

    Args:
        response_text: Raw response from LLM

    Returns:
        Integer score from 0 to 100
    """
    try:
        # Remove any whitespace
        response_text = response_text.strip()

        # Try to find a number in the response
        match = re.search(r'\b(\d+)\b', response_text)
        if match:
            score = int(match.group(1))
            # Ensure score is in valid range
            if 0 <= score <= 100:
                return score
            else:
                logger.warning(f"Score {score} out of range, clamping to 0-100")
                return max(0, min(100, score))
        else:
            logger.error(f"Could not parse score from response: {response_text}")
            raise ValueError(f"Could not parse score from response: {response_text}")

    except Exception as e:
        logger.error(f"Error parsing score: {str(e)}")
        # Default to 0 if parsing fails
        return 0
