from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.case_result import CaseResultCreate, CaseResultResponse, CaseResultScoreUpdate
from app.crud import case_result as case_result_crud
from app.crud import case_test as case_test_crud
from app.crud import case as case_crud
from app.services.auth_service import get_current_user, get_current_methodist
from app.models.user import User
from app.models.case import CaseStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/case-results", tags=["case-results"])


@router.post("/submit", response_model=CaseResultResponse, status_code=status.HTTP_201_CREATED)
def submit_answer(
    result_data: CaseResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit an answer to a case test question (students only).

    The answer will be automatically evaluated using AI and a score (0-100) will be assigned.

    Args:
        result_data: Answer submission data (test_id, answer)
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Created CaseResult with AI-evaluated score
    """
    # Get the test
    test = case_test_crud.get_case_test_by_id(db, test_id=result_data.test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test question not found"
        )

    # Get the case to check if it's published
    case = case_crud.get_case(db, case_id=test.case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Students can only submit answers to published cases
    if current_user.role.value == "student" and case.status != CaseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot submit answer to unpublished case"
        )

    # Validate that at least one of answer or file_url is provided
    if not result_data.answer and not result_data.file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either answer or file_url must be provided"
        )

    try:
        # Create the result with automatic evaluation
        logger.info(f"Student {current_user.id} submitting answer for test {result_data.test_id}")
        result = case_result_crud.create_case_result(
            db=db,
            result_data=result_data,
            student_id=current_user.id
        )
        logger.info(f"Answer submitted successfully with score: {result.score}")
        return result

    except ValueError as e:
        # Handle duplicate submission or test not found
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.get("/my-results", response_model=List[CaseResultResponse])
def get_my_results(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all results for the current user (student view).

    Returns:
        List of CaseResult objects for the current user
    """
    results = case_result_crud.get_student_results(
        db=db,
        student_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return results


@router.get("/my-result/test/{test_id}", response_model=CaseResultResponse)
def get_my_result_for_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's result for a specific test question.

    This is useful for students to check if they've already answered a question
    and to see their score.

    Args:
        test_id: ID of the test question
        db: Database session
        current_user: Currently authenticated user

    Returns:
        CaseResult object if found, otherwise 404
    """
    # Check if test exists
    test = case_test_crud.get_case_test_by_id(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test question not found"
        )

    # Get student's result for this test
    result = case_result_crud.get_student_result_for_test(
        db=db,
        test_id=test_id,
        student_id=current_user.id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't answered this question yet"
        )

    return result


@router.get("/test/{test_id}", response_model=List[CaseResultResponse])
def get_results_by_test(
    test_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Get all student results for a specific test question (methodist only).

    Args:
        test_id: ID of the test question
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        List of all student answers for this question
    """
    # Check if test exists
    test = case_test_crud.get_case_test_by_id(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test question not found"
        )

    results = case_result_crud.get_results_by_test(
        db=db,
        test_id=test_id,
        skip=skip,
        limit=limit
    )
    return results


@router.get("/case/{case_id}", response_model=List[CaseResultResponse])
def get_results_by_case(
    case_id: int,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Get all student results for all questions in a case (methodist only).

    Args:
        case_id: ID of the case
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        List of all student answers for all questions in this case
    """
    # Check if case exists
    case = case_crud.get_case(db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    results = case_result_crud.get_results_by_case(
        db=db,
        case_id=case_id,
        skip=skip,
        limit=limit
    )
    return results


@router.get("/{result_id}", response_model=CaseResultResponse)
def get_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific result by ID.

    Students can only view their own results.
    Methodists can view any result.

    Args:
        result_id: ID of the result
        db: Database session
        current_user: Currently authenticated user

    Returns:
        CaseResult object
    """
    result = case_result_crud.get_case_result_by_id(db, result_id=result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Students can only view their own results
    if current_user.role.value == "student" and result.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own results"
        )

    return result


@router.patch("/{result_id}/score", response_model=CaseResultResponse)
def update_result_score(
    result_id: int,
    score_update: CaseResultScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Update the score of a student's answer (methodist only).

    This allows methodists to manually adjust the AI-generated score
    or provide a score if automatic evaluation failed.

    Args:
        result_id: ID of the result to update
        score_update: New score value (0-100)
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        Updated CaseResult object with new score
    """
    # Check if result exists
    result = case_result_crud.get_case_result_by_id(db, result_id=result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Update the score
    updated_result = case_result_crud.update_case_result_score(
        db=db,
        result_id=result_id,
        new_score=score_update.score
    )

    if not updated_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update score"
        )

    logger.info(f"Methodist {current_user.id} updated score for result {result_id} to {score_update.score}")
    return updated_result


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Delete a result by ID (methodist only).

    Args:
        result_id: ID of the result to delete
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        204 No Content on success
    """
    result = case_result_crud.get_case_result_by_id(db, result_id=result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    deleted = case_result_crud.delete_case_result(db, result_id=result_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete result"
        )

    logger.info(f"Result {result_id} deleted by methodist {current_user.id}")
    return None
