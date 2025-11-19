from sqlalchemy.orm import Session
from app.models.test import Test
from typing import List, Dict, Any


def get_test(db: Session, test_id: int):
    return db.query(Test).filter(Test.id == test_id).first()


def get_test_by_course(db: Session, course_id: int):
    return db.query(Test).filter(Test.course_id == course_id).first()


def get_tests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Test).offset(skip).limit(limit).all()


def create_test(db: Session, course_id: int, questions: List[Dict[str, Any]]):
    # Check if test already exists for this course
    existing_test = get_test_by_course(db, course_id)
    if existing_test:
        # Update existing test
        existing_test.questions = questions
        db.commit()
        db.refresh(existing_test)
        return existing_test

    # Create new test
    db_test = Test(
        course_id=course_id,
        questions=questions
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test


def update_test(db: Session, test_id: int, questions: List[Dict[str, Any]]):
    db_test = get_test(db, test_id)
    if db_test:
        db_test.questions = questions
        db.commit()
        db.refresh(db_test)
        return db_test
    return None


def delete_test(db: Session, test_id: int):
    db_test = get_test(db, test_id)
    if db_test:
        db.delete(db_test)
        db.commit()
        return True
    return False
