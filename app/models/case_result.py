from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CaseResult(Base):
    """
    Model for storing student answers to case test questions.
    Each student can submit only one answer per question.
    """
    __tablename__ = "case_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("case_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answer = Column(Text, nullable=True)  # Text answer from student
    file_url = Column(String, nullable=True)  # URL to uploaded file (future feature)
    score = Column(Integer, nullable=True)  # AI-evaluated score (0-100)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    test = relationship("CaseTest", back_populates="results")
    student = relationship("User", back_populates="case_results")

    # Unique constraint: one answer per student per question
    __table_args__ = (
        UniqueConstraint('test_id', 'student_id', name='uq_test_student'),
    )
