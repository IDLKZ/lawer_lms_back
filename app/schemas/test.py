from pydantic import BaseModel
from datetime import datetime
from typing import List, Any, Optional


# Schema for a single question
class Question(BaseModel):
    question: str
    options: List[str]  # List of answer options
    correct_answer: str  # The actual correct answer (must be one of the options)


# Schema for a question without the correct answer (for students)
class QuestionForStudent(BaseModel):
    id: int  # Index of the question
    question: str
    options: List[str]


# Schema for creating a test
class TestCreate(BaseModel):
    course_id: int
    questions: Optional[List[Question]] | None = None


# Schema for updating a test
class TestUpdate(BaseModel):
    questions: List[Question]


# Schema for test in responses (with correct answers - for methodist)
class Test(BaseModel):
    id: int
    course_id: int
    questions: List[Question]
    created_at: datetime

    class Config:
        from_attributes = True


# Schema for test for students (without correct answers)
class TestForStudent(BaseModel):
    id: int
    course_id: int
    questions: List[QuestionForStudent]
    created_at: datetime

    class Config:
        from_attributes = True


# Schema for submitting answers
class AnswerSubmit(BaseModel):
    question_id: int  # Index of the question (0-based)
    selected_answer: str  # The actual answer text selected by the student


class TestSubmit(BaseModel):
    answers: List[AnswerSubmit]
