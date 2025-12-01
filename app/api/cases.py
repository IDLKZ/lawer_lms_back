from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.case import (
    Case,
    CaseCreate,
    CaseUpdate,
    CaseSummary,
    PDFProcessingResult,
    CaseFromPDF,
    PDFValidationResult
)
from app.schemas.case_test import CaseTestResponse, CaseTestStudentResponse
from app.crud import case as case_crud
from app.crud import case_test as case_test_crud
from app.services.auth_service import get_current_methodist, get_current_user
from app.models.user import User
from app.models.case import CaseStatus
from app.services.pdf_service import (
    process_pdf_with_llm,
    validate_pdf_file
)
from app.services.case_questions_service import generate_case_questions
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/upload-pdf", response_model=PDFProcessingResult)
async def upload_and_process_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_methodist)
):
    """
    Upload a PDF file and process it with Ollama LLM to remove personal data.

    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text from the PDF
    3. Uses Ollama LLM to detect and remove personal information
    4. Replaces personal data with placeholders like "Гражданин А.", "Офицер Б."

    Args:
        file: PDF file to upload

    Returns:
        PDFProcessingResult with original text, cleaned text, and metadata
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    try:
        # Read file content
        pdf_bytes = await file.read()

        # Validate PDF
        validation_result = validate_pdf_file(pdf_bytes)
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid PDF file: {validation_result['error']}"
            )

        logger.info(f"Processing PDF: {file.filename} ({validation_result['page_count']} pages)")

        # Process PDF with LLM (Ollama or cloud)
        result = process_pdf_with_llm(
            pdf_bytes,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            ollama_url=settings.OLLAMA_URL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return PDFProcessingResult(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.post("/validate-pdf", response_model=PDFValidationResult)
async def validate_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_methodist)
):
    """
    Validate a PDF file before processing.

    Returns information about the PDF file without processing it.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    try:
        pdf_bytes = await file.read()
        validation_result = validate_pdf_file(pdf_bytes)
        return PDFValidationResult(**validation_result)

    except Exception as e:
        logger.error(f"Error validating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate PDF: {str(e)}"
        )


@router.post("/from-pdf", response_model=Case, status_code=status.HTTP_201_CREATED)
async def create_case_from_pdf(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    status_value: str = Form("draft"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Upload a PDF, process it with Ollama LLM, and create a case in one step.

    This is a convenience endpoint that combines PDF processing and case creation.

    Args:
        file: PDF file to upload
        title: Title for the case
        description: Optional description
        status_value: Case status (draft/published)

    Returns:
        The created Case object
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    try:
        # Read and process PDF
        pdf_bytes = await file.read()
        result = process_pdf_with_llm(
            pdf_bytes,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            ollama_url=settings.OLLAMA_URL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            use_ner=settings.LLM_USE_NER
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        # Parse status
        try:
            case_status = CaseStatus.PUBLISHED if status_value.lower() == "published" else CaseStatus.DRAFT
        except:
            case_status = CaseStatus.DRAFT

        # Create case from PDF
        case_data = CaseFromPDF(
            title=title,
            description=description,
            cleaned_text=result["cleaned_text"],
            status=case_status
        )

        return case_crud.create_case_from_pdf(
            db=db,
            case_data=case_data,
            creator_id=current_user.id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating case from PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case from PDF: {str(e)}"
        )


@router.post("", response_model=Case, status_code=status.HTTP_201_CREATED)
def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Create a new case manually (without PDF upload).

    Methodist can provide case data directly.
    """
    return case_crud.create_case(db=db, case=case, creator_id=current_user.id)


@router.get("", response_model=List[CaseSummary])
def get_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of cases.
    - Methodists see all cases
    - Students see only published cases
    """
    if current_user.role.value == "methodist":
        # Methodist sees all cases
        cases = case_crud.get_cases(db, skip=skip, limit=limit)
    else:
        # Student sees only published cases
        cases = case_crud.get_cases(
            db, skip=skip, limit=limit, status=CaseStatus.PUBLISHED
        )
    return cases


@router.get("/{case_id}", response_model=Case)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific case.
    """
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Students can only access published cases
    if current_user.role.value == "student" and case.status != CaseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to unpublished case"
        )

    return case


@router.patch("/{case_id}", response_model=Case)
def update_case(
    case_id: int,
    case_update: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Update case information (methodist only).
    """
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if the current user is the creator of the case
    if case.created_by and case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own cases"
        )

    return case_crud.update_case(db=db, case_id=case_id, case_update=case_update)


@router.post("/{case_id}/publish", response_model=Case)
def publish_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Publish a case (change status to PUBLISHED).
    """
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if the current user is the creator
    if case.created_by and case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own cases"
        )

    return case_crud.publish_case(db=db, case_id=case_id)


@router.post("/{case_id}/unpublish", response_model=Case)
def unpublish_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Unpublish a case (change status back to DRAFT).
    """
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if the current user is the creator
    if case.created_by and case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unpublish your own cases"
        )

    return case_crud.unpublish_case(db=db, case_id=case_id)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Delete a case (methodist only).
    """
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if the current user is the creator
    if case.created_by and case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own cases"
        )

    case_crud.delete_case(db=db, case_id=case_id)
    return None


@router.post("/{case_id}/generate-questions", response_model=List[CaseTestResponse])
def generate_questions_for_case(
    case_id: int,
    count: int = Query(default=5, ge=1, le=20, description="Number of questions to generate"),
    field_of_law: str = Query(default="уголовный процесс", description="Area of law"),
    target_audience: str = Query(default="студенты бакалавриата", description="Target audience"),
    jurisdiction: str = Query(default="Республика Казахстан, континентальная система", description="Legal jurisdiction"),
    difficulty_level: str = Query(default="базовый", description="Difficulty level: базовый, продвинутый, экспертный"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Generate educational questions for a case using LLM (openai/gpt-5.1).

    This endpoint creates detailed questions with comprehensive answers (300-700 words)
    suitable for legal education.

    The endpoint:
    1. Retrieves the case by ID
    2. Uses the cleaned_text from the case
    3. Generates questions using advanced LLM (openai/gpt-5.1)
    4. Saves the generated questions with detailed answers to the database
    5. Returns the list of created questions

    Args:
        case_id: ID of the case
        count: Number of questions to generate (default: 5, max: 20)
        field_of_law: Area of law (e.g., "уголовный процесс", "гражданское право")
        target_audience: Target audience (e.g., "студенты бакалавриата", "магистранты")
        jurisdiction: Legal jurisdiction (default: "Республика Казахстан")
        difficulty_level: Difficulty level ("базовый", "продвинутый", "экспертный")
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        List of generated CaseTestResponse objects with detailed answers
    """
    # Get the case
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if case has cleaned_text
    if not case.cleaning_text or len(case.cleaning_text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case does not have cleaned text. Please process the case first."
        )

    try:
        logger.info(f"Generating {count} educational questions for case ID {case_id}")
        logger.info(f"Parameters: field={field_of_law}, audience={target_audience}, "
                   f"jurisdiction={jurisdiction}, difficulty={difficulty_level}")

        # Generate questions using specialized case questions service
        questions_data = generate_case_questions(
            case_text=case.cleaning_text,
            num_questions=count,
            field_of_law=field_of_law,
            target_audience=target_audience,
            jurisdiction=jurisdiction,
            difficulty_level=difficulty_level
        )

        if not questions_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate questions. LLM returned empty response."
            )

        logger.info(f"Generated {len(questions_data)} questions successfully")

        # The service already returns data in the correct format:
        # [{"question": "...", "answer": "..."}]
        # No transformation needed

        # Save to database using bulk insert
        created_tests = case_test_crud.create_case_tests_bulk(
            db=db,
            case_id=case_id,
            questions_data=questions_data,
            created_by=current_user.id
        )

        logger.info(f"Saved {len(created_tests)} questions to database")

        return created_tests

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions for case {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.get("/{case_id}/questions")
def get_case_questions(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all generated questions for a specific case.

    - Methodists see questions WITH correct answers
    - Students see questions WITHOUT correct answers

    Args:
        case_id: ID of the case
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of questions (with or without answers depending on role)
    """
    # Check if case exists
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Students can only access published cases
    if current_user.role.value == "student" and case.status != CaseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to unpublished case"
        )

    # Get all questions for this case
    questions = case_test_crud.get_case_tests_by_case_id(db, case_id=case_id)

    # Return different response based on role
    if current_user.role.value == "methodist":
        # Methodists see full questions with answers
        return [
            {
                "id": q.id,
                "case_id": q.case_id,
                "question": q.question,
                "answer": q.answer,
                "created_by": q.created_by,
                "created_at": q.created_at,
                "updated_at": q.updated_at
            }
            for q in questions
        ]
    else:
        # Students see questions without answers
        return [
            {
                "id": q.id,
                "case_id": q.case_id,
                "question": q.question,
                "created_at": q.created_at,
                "updated_at": q.updated_at
            }
            for q in questions
        ]


@router.delete("/{case_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case_question(
    case_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Delete a specific question for a case (methodist only).

    Args:
        case_id: ID of the case
        question_id: ID of the question to delete
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        204 No Content on success
    """
    # Check if case exists
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Get the question
    question = case_test_crud.get_case_test_by_id(db, test_id=question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Verify that the question belongs to the specified case
    if question.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question {question_id} does not belong to case {case_id}"
        )

    # Check if the current user is the creator of the question
    if question.created_by and question.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete questions you created"
        )

    # Delete the question
    deleted = case_test_crud.delete_case_test(db, test_id=question_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete question"
        )

    logger.info(f"Question {question_id} deleted by user {current_user.id}")
    return None
