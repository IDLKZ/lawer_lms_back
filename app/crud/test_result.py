from sqlalchemy.orm import Session, joinedload
from app.models.test_result import TestResult
from typing import List, Dict, Any


def get_test_result(db: Session, result_id: int):
    """Get test result with eager loaded test and student."""
    return db.query(TestResult).options(
        joinedload(TestResult.test),
        joinedload(TestResult.student)
    ).filter(TestResult.id == result_id).first()


def get_test_results(db: Session, skip: int = 0, limit: int = 100, course_id: int = None):
    """
    Get all test results with eager loaded test and student.
    Optionally filter by course_id.
    """
    from app.models.test import Test

    query = db.query(TestResult).options(
        joinedload(TestResult.test),
        joinedload(TestResult.student)
    )

    # Filter by course_id if provided
    if course_id is not None:
        query = query.join(Test, TestResult.test_id == Test.id).filter(
            Test.course_id == course_id
        )

    return query.offset(skip).limit(limit).all()


def get_test_results_by_student(
    db: Session,
    student_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Get test results by student with eager loaded test and student."""
    return db.query(TestResult).options(
        joinedload(TestResult.test),
        joinedload(TestResult.student)
    ).filter(
        TestResult.student_id == student_id
    ).offset(skip).limit(limit).all()


def get_test_results_by_test(
    db: Session,
    test_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Get test results by test with eager loaded test and student."""
    return db.query(TestResult).options(
        joinedload(TestResult.test),
        joinedload(TestResult.student)
    ).filter(
        TestResult.test_id == test_id
    ).offset(skip).limit(limit).all()


def get_test_results_by_student_and_course(
    db: Session,
    student_id: int,
    course_id: int
):
    """
    Get all test results for a specific student and course.
    Joins TestResult with Test to filter by course_id.
    Eager loads test and student relationships.
    """
    from app.models.test import Test

    return db.query(TestResult).options(
        joinedload(TestResult.test),
        joinedload(TestResult.student)
    ).join(
        Test, TestResult.test_id == Test.id
    ).filter(
        TestResult.student_id == student_id,
        Test.course_id == course_id
    ).all()


def get_test_result_by_student_and_test(
    db: Session,
    student_id: int,
    test_id: int
):
    """
    Get test result for a specific student and test.
    Returns None if not found.
    Eager loads test and student relationships.
    """
    return db.query(TestResult).options(
        joinedload(TestResult.test),
        joinedload(TestResult.student)
    ).filter(
        TestResult.student_id == student_id,
        TestResult.test_id == test_id
    ).first()


def create_test_result(
    db: Session,
    test_id: int,
    student_id: int,
    answers: List[Dict[str, Any]],
    score: int,
    total_questions: int
):
    db_result = TestResult(
        test_id=test_id,
        student_id=student_id,
        answers=answers,
        score=score,
        total_questions=total_questions
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def update_test_result(
    db: Session,
    result_id: int,
    answers: List[Dict[str, Any]],
    score: int,
    total_questions: int
):
    """
    Update an existing test result.
    """
    db_result = get_test_result(db, result_id)
    if db_result:
        db_result.answers = answers
        db_result.score = score
        db_result.total_questions = total_questions
        # submitted_at will be automatically updated if you have onupdate in the model
        db.commit()
        db.refresh(db_result)
        return db_result
    return None


def create_or_update_test_result(
    db: Session,
    test_id: int,
    student_id: int,
    answers: List[Dict[str, Any]],
    score: int,
    total_questions: int
):
    """
    Create a new test result or update existing one if student already took this test.
    """
    # Check if result already exists
    existing_result = get_test_result_by_student_and_test(db, student_id, test_id)

    if existing_result:
        # Update existing result
        return update_test_result(
            db=db,
            result_id=existing_result.id,
            answers=answers,
            score=score,
            total_questions=total_questions
        )
    else:
        # Create new result
        return create_test_result(
            db=db,
            test_id=test_id,
            student_id=student_id,
            answers=answers,
            score=score,
            total_questions=total_questions
        )


def delete_test_result(db: Session, result_id: int):
    db_result = get_test_result(db, result_id)
    if db_result:
        db.delete(db_result)
        db.commit()
        return True
    return False
