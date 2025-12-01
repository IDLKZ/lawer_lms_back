from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CaseTest(Base):
    """
    Model for case test questions generated from case documents.

    These questions are automatically generated based on the cleaned case text
    and can be used for assessment or training purposes.
    """
    __tablename__ = "case_tests"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="case_tests")
    case = relationship("Case", back_populates="case_tests")
    results = relationship("CaseResult", back_populates="test", cascade="all, delete-orphan")
