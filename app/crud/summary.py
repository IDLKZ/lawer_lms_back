from sqlalchemy.orm import Session
from app.models.summary import Summary


def get_summary(db: Session, summary_id: int):
    return db.query(Summary).filter(Summary.id == summary_id).first()


def get_summary_by_course(db: Session, course_id: int):
    return db.query(Summary).filter(Summary.course_id == course_id).first()


def get_summaries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Summary).offset(skip).limit(limit).all()


def create_summary(db: Session, course_id: int, content: str):
    # Check if summary already exists for this course
    existing_summary = get_summary_by_course(db, course_id)
    if existing_summary:
        # Update existing summary
        existing_summary.content = content
        db.commit()
        db.refresh(existing_summary)
        return existing_summary

    # Create new summary
    db_summary = Summary(
        course_id=course_id,
        content=content
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary


def update_summary(db: Session, summary_id: int, content: str):
    db_summary = get_summary(db, summary_id)
    if db_summary:
        db_summary.content = content
        db.commit()
        db.refresh(db_summary)
        return db_summary
    return None


def delete_summary(db: Session, summary_id: int):
    db_summary = get_summary(db, summary_id)
    if db_summary:
        db.delete(db_summary)
        db.commit()
        return True
    return False
