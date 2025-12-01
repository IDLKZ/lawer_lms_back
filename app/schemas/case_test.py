from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Base schema
class CaseTestBase(BaseModel):
    question: str
    answer: str


# Schema for creating a case test
class CaseTestCreate(CaseTestBase):
    case_id: int


# Schema for case test in responses (with answer - for methodists)
class CaseTestResponse(CaseTestBase):
    id: int
    case_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for students (without answer field)
class CaseTestStudentResponse(BaseModel):
    id: int
    case_id: int
    question: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
