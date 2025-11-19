from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    original_text = Column(Text, nullable=True)  # Optional: text content
    file_url = Column(String, nullable=True)  # Optional: URL to file in Supabase
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="courses")
    summaries = relationship("Summary", back_populates="course", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="course", cascade="all, delete-orphan")
