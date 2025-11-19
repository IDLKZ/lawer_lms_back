from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.summary import Summary, SummaryCreate
from app.schemas.test import Test, TestCreate
from app.crud import course as course_crud
from app.crud import summary as summary_crud
from app.crud import test as test_crud
from app.services.auth_service import get_current_methodist
from app.services.llm_service import generate_summary, generate_test
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-summary", response_model=Summary)
def create_summary(
    summary_request: SummaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Generate a summary/конспект for a course using OpenAI (methodist only).

    This endpoint:
    1. Gets the course content (original_text or file_url)
    2. Sends it to OpenAI API for summarization
    3. Saves the generated summary to the database

    Works with both text and file-based courses.
    """
    # Get the course
    course = course_crud.get_course(db, course_id=summary_request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate summary for this course"
        )

    # Check that course has either text or file_url
    if not course.original_text and not course.file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must have either original_text or file_url"
        )

    try:
        # Generate summary using OpenAI (from text or file)
        summary_content = generate_summary(
            text=course.original_text,
            file_url=course.file_url
        )
        print(f"summary_content: {summary_content}")

        # Save summary to database
        db_summary = summary_crud.create_summary(
            db=db,
            course_id=summary_request.course_id,
            content=summary_content
        )

        return db_summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/generate-test", response_model=Test)
def create_test(
    test_request: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Generate a test with multiple choice questions for a course using OpenAI (methodist only).

    This endpoint:
    1. Gets the course original text
    2. Sends it to OpenAI API to generate 5 multiple choice questions
    3. Saves the generated test to the database

    The test format: [{question, options: [list of answers], correct_answer: actual answer text}]
    Note: correct_answer contains the full text of the correct answer, not a letter.
    """
    # Get the course
    course = course_crud.get_course(db, course_id=test_request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate test for this course"
        )

    # Check that course has either text or file_url
    if not course.original_text and not course.file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must have either original_text or file_url"
        )

    try:
        # Generate test questions using OpenAI (from text or file)
        questions = generate_test(
            text=course.original_text,
            file_url=course.file_url,
            num_questions=5
        )

        # Save test to database
        db_test = test_crud.create_test(
            db=db,
            course_id=test_request.course_id,
            questions=questions
        )

        return db_test

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test: {str(e)}"
        )
