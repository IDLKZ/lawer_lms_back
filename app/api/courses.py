from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.course import Course, CourseCreate, CourseUpdate, CourseSummary
from app.crud import course as course_crud
from app.services.auth_service import get_current_methodist, get_current_user
from app.models.user import User
from app.models.course import CourseStatus

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=Course, status_code=status.HTTP_201_CREATED)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Create a new course (methodist only).

    Methodist can provide course content in two ways:
    1. Text content: Pass 'original_text' with the full text
    2. File URL: Upload file to Supabase first, then pass 'file_url'

    At least one of 'original_text' or 'file_url' must be provided.
    Both can be provided simultaneously if needed.
    """
    return course_crud.create_course(db=db, course=course, creator_id=current_user.id)


@router.get("", response_model=List[CourseSummary])
def get_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of courses.
    - Methodists see all courses
    - Students see only published courses
    """
    if current_user.role.value == "methodist":
        # Methodist sees all courses
        courses = course_crud.get_courses(db, skip=skip, limit=limit)
    else:
        # Student sees only published courses
        courses = course_crud.get_courses(
            db, skip=skip, limit=limit, status=CourseStatus.PUBLISHED
        )
    return courses


@router.get("/{course_id}", response_model=Course)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific course.
    """
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Students can only access published courses
    if current_user.role.value == "student" and course.status != CourseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to unpublished course"
        )

    return course


@router.patch("/{course_id}", response_model=Course)
def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Update course information (methodist only).
    """
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this course"
        )

    updated_course = course_crud.update_course(db, course_id=course_id, course_update=course_update)
    return updated_course


@router.patch("/{course_id}/publish", response_model=Course)
def publish_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Publish a course to make it available to students (methodist only).
    """
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to publish this course"
        )

    published_course = course_crud.publish_course(db, course_id=course_id)
    return published_course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Delete a course (methodist only).
    Only the creator of the course can delete it.
    """
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this course"
        )

    success = course_crud.delete_course(db, course_id=course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )

    return None
