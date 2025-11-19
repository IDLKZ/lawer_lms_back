from pydantic import BaseModel
from datetime import datetime


# Schema for creating a summary
class SummaryCreate(BaseModel):
    course_id: int
    content: str


# Schema for updating a summary
class SummaryUpdate(BaseModel):
    content: str


# Schema for summary in responses
class Summary(BaseModel):
    id: int
    course_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
