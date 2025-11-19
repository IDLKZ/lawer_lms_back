from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    questions = Column(JSON, nullable=False)  # Format: [{question, options: [list of answers], correct_answer: actual answer}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="tests")
    results = relationship("TestResult", back_populates="test", cascade="all, delete-orphan")
