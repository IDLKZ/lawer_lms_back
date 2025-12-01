from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# Base schema
class CaseResultBase(BaseModel):
    answer: Optional[str] = None
    file_url: Optional[str] = None


# Schema for creating a case result (student submission)
class CaseResultCreate(BaseModel):
    test_id: int
    answer: Optional[str] = Field(None, description="Text answer from student")
    file_url: Optional[str] = Field(None, description="URL to uploaded file (future feature)")

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": 1,
                "answer": "В данном случае применяется статья 189 УПК РК..."
            }
        }


# Schema for updating score (methodist only)
class CaseResultScoreUpdate(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Score from 0 to 100")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 85
            }
        }


# Schema for case result in responses
class CaseResultResponse(CaseResultBase):
    id: int
    test_id: int
    student_id: int
    score: Optional[int] = Field(None, description="AI-evaluated score (0-100)")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema with additional details (for methodist view)
class CaseResultDetail(CaseResultResponse):
    student_name: Optional[str] = Field(None, description="Full name of the student")
    question: Optional[str] = Field(None, description="The question text")
    correct_answer: Optional[str] = Field(None, description="The correct answer from case_test")

    class Config:
        from_attributes = True
