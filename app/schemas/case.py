from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Dict, List, Any
from app.models.case import CaseStatus


# Base schema
class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None


# Schema for creating a case (manual creation without PDF)
class CaseCreate(CaseBase):
    cleaning_text: Optional[str] = None
    status: Optional[CaseStatus] = CaseStatus.DRAFT


# Schema for updating a case
class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cleaning_text: Optional[str] = None
    status: Optional[CaseStatus] = None


# Schema for case in responses
class Case(CaseBase):
    id: int
    cleaning_text: Optional[str] = None
    created_by: Optional[int] = None
    status: CaseStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for case summary (without full text)
class CaseSummary(CaseBase):
    id: int
    created_by: Optional[int] = None
    status: CaseStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for PDF upload response
class PDFProcessingResult(BaseModel):
    """Response after processing a PDF file with NER + LLM pipeline"""
    original_text: str
    cleaned_text: str
    preprocessed_text: Optional[str] = None  # Text after NER preprocessing
    original_length: int
    cleaned_length: int
    llm_model: str
    ner_stats: Optional[Dict[str, Any]] = None  # Statistics from NER preprocessing
    pipeline_used: Optional[str] = None  # "NER + LLM" or "LLM Only"
    success: bool
    error: Optional[str] = None
    chunks_processed: Optional[int] = None


# Schema for case creation from PDF
class CaseFromPDF(BaseModel):
    """Schema for creating a case from a processed PDF"""
    title: str
    description: Optional[str] = None
    cleaned_text: str
    status: Optional[CaseStatus] = CaseStatus.DRAFT


# Schema for PDF validation result
class PDFValidationResult(BaseModel):
    """Result of PDF validation"""
    is_valid: bool
    page_count: int
    file_size: int
    error: Optional[str] = None
