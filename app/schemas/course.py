from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from app.models.course import CourseStatus


# Base schema
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None


# Schema for creating a course
class CourseCreate(CourseBase):
    original_text: Optional[str] = None  # Text content (optional)
    file_url: Optional[str] = None  # URL to file in Supabase (optional)

    @field_validator('file_url', 'original_text')
    @classmethod
    def validate_content(cls, v, info):
        # This validator is called after all fields are processed
        # We need to check if at least one is provided
        return v

    def model_post_init(self, __context):
        # Check that at least one of original_text or file_url is provided
        if not self.original_text and not self.file_url:
            raise ValueError("Either 'original_text' or 'file_url' must be provided")


# Schema for updating a course
class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    original_text: Optional[str] = None
    file_url: Optional[str] = None
    status: Optional[CourseStatus] = None


# Schema for course in responses
class Course(CourseBase):
    id: int
    original_text: Optional[str] = None
    file_url: Optional[str] = None
    created_by: int
    status: CourseStatus
    created_at: datetime

    class Config:
        from_attributes = True


# Schema for course summary (without full original_text)
class CourseSummary(CourseBase):
    id: int
    created_by: int
    status: CourseStatus
    created_at: datetime

    class Config:
        from_attributes = True
