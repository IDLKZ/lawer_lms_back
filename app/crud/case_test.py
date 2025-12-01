from sqlalchemy.orm import Session
from typing import List, Dict
from app.models.case_test import CaseTest
from app.schemas.case_test import CaseTestCreate


def create_case_test(
    db: Session,
    case_id: int,
    question: str,
    answer: str,
    created_by: int
) -> CaseTest:
    """
    Create a single case test question.

    Args:
        db: Database session
        case_id: ID of the case
        question: Test question text
        answer: Expected answer text
        created_by: User ID who created this test

    Returns:
        Created CaseTest object
    """
    db_case_test = CaseTest(
        case_id=case_id,
        question=question,
        answer=answer,
        created_by=created_by
    )
    db.add(db_case_test)
    db.commit()
    db.refresh(db_case_test)
    return db_case_test


def create_case_tests_bulk(
    db: Session,
    case_id: int,
    questions_data: List[Dict[str, str]],
    created_by: int
) -> List[CaseTest]:
    """
    Create multiple case test questions in bulk.

    Args:
        db: Database session
        case_id: ID of the case
        questions_data: List of dicts with 'question' and 'answer' keys
        created_by: User ID who created these tests

    Returns:
        List of created CaseTest objects
    """
    case_tests = []
    for item in questions_data:
        db_case_test = CaseTest(
            case_id=case_id,
            question=item["question"],
            answer=item["answer"],
            created_by=created_by
        )
        db.add(db_case_test)
        case_tests.append(db_case_test)

    db.commit()

    # Refresh all objects to get their IDs and timestamps
    for case_test in case_tests:
        db.refresh(case_test)

    return case_tests


def get_case_tests_by_case_id(
    db: Session,
    case_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[CaseTest]:
    """
    Get all test questions for a specific case.

    Args:
        db: Database session
        case_id: ID of the case
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of CaseTest objects
    """
    return db.query(CaseTest).filter(
        CaseTest.case_id == case_id
    ).offset(skip).limit(limit).all()


def get_case_test_by_id(db: Session, test_id: int) -> CaseTest:
    """
    Get a specific case test by its ID.

    Args:
        db: Database session
        test_id: ID of the case test

    Returns:
        CaseTest object or None if not found
    """
    return db.query(CaseTest).filter(CaseTest.id == test_id).first()


def delete_case_test(db: Session, test_id: int) -> bool:
    """
    Delete a case test by its ID.

    Args:
        db: Database session
        test_id: ID of the case test

    Returns:
        True if deleted, False if not found
    """
    case_test = db.query(CaseTest).filter(CaseTest.id == test_id).first()
    if case_test:
        db.delete(case_test)
        db.commit()
        return True
    return False


def delete_case_tests_by_case_id(db: Session, case_id: int) -> int:
    """
    Delete all test questions for a specific case.

    Args:
        db: Database session
        case_id: ID of the case

    Returns:
        Number of deleted records
    """
    deleted_count = db.query(CaseTest).filter(
        CaseTest.case_id == case_id
    ).delete()
    db.commit()
    return deleted_count
