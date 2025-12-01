from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models.case_result import CaseResult
from app.models.case_test import CaseTest
from app.models.user import User
from app.schemas.case_result import CaseResultCreate
from app.services.answer_evaluation_service import evaluate_answer
import logging

logger = logging.getLogger(__name__)


def create_case_result(
    db: Session,
    result_data: CaseResultCreate,
    student_id: int
) -> CaseResult:
    """
    Create a case result (student answer) with automatic AI evaluation.

    Args:
        db: Database session
        result_data: Result creation data
        student_id: ID of the student submitting the answer

    Returns:
        Created CaseResult object with score

    Raises:
        ValueError: If test not found or student already answered
    """
    # Get the test question to retrieve correct answer
    test = db.query(CaseTest).filter(CaseTest.id == result_data.test_id).first()
    if not test:
        raise ValueError(f"Test with ID {result_data.test_id} not found")

    # Check if student already answered this question
    existing = db.query(CaseResult).filter(
        CaseResult.test_id == result_data.test_id,
        CaseResult.student_id == student_id
    ).first()

    if existing:
        raise ValueError(f"Student already submitted answer for test {result_data.test_id}")

    # Evaluate the answer using LLM
    score = None
    if result_data.answer:
        try:
            logger.info(f"Evaluating answer for test {result_data.test_id}")
            score = evaluate_answer(
                student_answer=result_data.answer,
                correct_answer=test.answer,
                question=test.question
            )
            logger.info(f"Answer evaluated with score: {score}")
        except Exception as e:
            logger.error(f"Failed to evaluate answer: {str(e)}")
            # Continue without score if evaluation fails
            score = None

    # Create the result
    db_result = CaseResult(
        test_id=result_data.test_id,
        student_id=student_id,
        answer=result_data.answer,
        file_url=result_data.file_url,
        score=score
    )

    db.add(db_result)
    db.commit()
    db.refresh(db_result)

    return db_result


def get_case_result_by_id(db: Session, result_id: int) -> Optional[CaseResult]:
    """
    Get a specific case result by its ID.

    Args:
        db: Database session
        result_id: ID of the case result

    Returns:
        CaseResult object or None if not found
    """
    return db.query(CaseResult).filter(CaseResult.id == result_id).first()


def get_student_results(
    db: Session,
    student_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[CaseResult]:
    """
    Get all results for a specific student.

    Args:
        db: Database session
        student_id: ID of the student
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of CaseResult objects
    """
    return db.query(CaseResult).filter(
        CaseResult.student_id == student_id
    ).offset(skip).limit(limit).all()


def get_results_by_test(
    db: Session,
    test_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[CaseResult]:
    """
    Get all student results for a specific test question.

    Args:
        db: Database session
        test_id: ID of the test question
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of CaseResult objects
    """
    return db.query(CaseResult).filter(
        CaseResult.test_id == test_id
    ).offset(skip).limit(limit).all()


def get_results_by_case(
    db: Session,
    case_id: int,
    skip: int = 0,
    limit: int = 1000
) -> List[CaseResult]:
    """
    Get all student results for all questions in a case.

    Args:
        db: Database session
        case_id: ID of the case
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of CaseResult objects
    """
    return db.query(CaseResult).join(
        CaseTest, CaseResult.test_id == CaseTest.id
    ).filter(
        CaseTest.case_id == case_id
    ).offset(skip).limit(limit).all()


def get_student_result_for_test(
    db: Session,
    test_id: int,
    student_id: int
) -> Optional[CaseResult]:
    """
    Get a specific student's result for a specific test.

    Args:
        db: Database session
        test_id: ID of the test question
        student_id: ID of the student

    Returns:
        CaseResult object or None if not found
    """
    return db.query(CaseResult).filter(
        CaseResult.test_id == test_id,
        CaseResult.student_id == student_id
    ).first()


def update_case_result_score(
    db: Session,
    result_id: int,
    new_score: int
) -> Optional[CaseResult]:
    """
    Update the score of a case result (methodist only).

    Args:
        db: Database session
        result_id: ID of the case result
        new_score: New score value (0-100)

    Returns:
        Updated CaseResult object or None if not found
    """
    result = db.query(CaseResult).filter(CaseResult.id == result_id).first()
    if result:
        result.score = new_score
        db.commit()
        db.refresh(result)
        logger.info(f"Score updated for result {result_id}: {new_score}")
        return result
    return None


def delete_case_result(db: Session, result_id: int) -> bool:
    """
    Delete a case result by its ID.

    Args:
        db: Database session
        result_id: ID of the case result

    Returns:
        True if deleted, False if not found
    """
    result = db.query(CaseResult).filter(CaseResult.id == result_id).first()
    if result:
        db.delete(result)
        db.commit()
        return True
    return False
