from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers = Column(JSON, nullable=False)  # Format: [{question_id, selected_answer, is_correct}]
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships with eager loading
    test = relationship("Test", back_populates="results", lazy="joined")
    student = relationship("User", back_populates="test_results", lazy="joined")
