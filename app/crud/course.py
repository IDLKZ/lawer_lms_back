from sqlalchemy.orm import Session
from app.models.course import Course, CourseStatus
from app.schemas.course import CourseCreate, CourseUpdate
from typing import Optional


def get_course(db: Session, course_id: int):
    return db.query(Course).filter(Course.id == course_id).first()


def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[CourseStatus] = None
):
    query = db.query(Course)
    if status:
        query = query.filter(Course.status == status)
    return query.offset(skip).limit(limit).all()


def get_courses_by_creator(
    db: Session,
    creator_id: int,
    skip: int = 0,
    limit: int = 100
):
    return db.query(Course).filter(
        Course.created_by == creator_id
    ).offset(skip).limit(limit).all()


def create_course(db: Session, course: CourseCreate, creator_id: int):
    db_course = Course(
        title=course.title,
        description=course.description,
        original_text=course.original_text,
        file_url=course.file_url,
        created_by=creator_id,
        status=CourseStatus.DRAFT
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(db: Session, course_id: int, course_update: CourseUpdate):
    db_course = get_course(db, course_id)
    if not db_course:
        return None

    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)

    db.commit()
    db.refresh(db_course)
    return db_course


def publish_course(db: Session, course_id: int):
    db_course = get_course(db, course_id)
    if not db_course:
        return None

    db_course.status = CourseStatus.PUBLISHED
    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: int):
    db_course = get_course(db, course_id)
    if db_course:
        db.delete(db_course)
        db.commit()
        return True
    return False
