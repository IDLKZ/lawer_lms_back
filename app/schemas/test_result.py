from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Any, Optional
from app.models.user import UserRole


# Schema for detailed answer with question info
class DetailedAnswer(BaseModel):
    question_id: int
    question: str
    options: List[str]
    selected_answer: str
    correct_answer: str
    is_correct: bool


# Nested schema for student info (to avoid circular imports)
class StudentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole


# Nested schema for test info (simplified)
class TestInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    created_at: datetime


# Schema for test result in responses (basic)
class TestResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    student_id: int
    answers: List[Any]  # [{question_id, selected_answer, is_correct}]
    score: int
    total_questions: int
    submitted_at: datetime


# Schema for test result with full relations
class TestResultWithRelations(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    student_id: int
    answers: List[Any]  # [{question_id, selected_answer, is_correct}]
    score: int
    total_questions: int
    submitted_at: datetime
    # Eager loaded relationships
    test: TestInfo
    student: StudentInfo


# Schema for detailed test result with full question information
class TestResultDetailed(BaseModel):
    id: int
    test_id: int
    student_id: int
    answers: List[DetailedAnswer]  # Full details including questions and correct answers
    score: int
    total_questions: int
    submitted_at: datetime
    percentage: float
    passed: bool


# Schema for test submission response
class TestSubmitResponse(BaseModel):
    score: int
    total: int
    passed: bool
    percentage: float
