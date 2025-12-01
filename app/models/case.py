from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class CaseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cleaning_text = Column(Text, nullable=True)  # Cleaned text after NER processing
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="cases")
    case_tests = relationship("CaseTest", back_populates="case", cascade="all, delete-orphan")
