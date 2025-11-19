from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.summary import Summary, SummaryCreate, SummaryUpdate
from app.crud import summary as summary_crud
from app.crud import course as course_crud
from app.services.auth_service import get_current_methodist, get_current_user
from app.models.user import User
from app.models.course import CourseStatus

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("", response_model=List[Summary])
def get_summaries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of summaries.
    - Methodists see all summaries
    - Students see only summaries for published courses
    """
    summaries = summary_crud.get_summaries(db, skip=skip, limit=limit)

    # If student, filter only summaries for published courses
    if current_user.role.value == "student":
        filtered_summaries = []
        for summary in summaries:
            course = course_crud.get_course(db, course_id=summary.course_id)
            if course and course.status == CourseStatus.PUBLISHED:
                filtered_summaries.append(summary)
        return filtered_summaries

    return summaries


@router.get("/course/{course_id}", response_model=Summary)
def get_summary_by_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary for a specific course.
    Students can only access summaries for published courses.
    """
    # Check if course exists
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

    # Get summary
    summary = summary_crud.get_summary_by_course(db, course_id=course_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found for this course"
        )

    return summary


@router.get("/{summary_id}", response_model=Summary)
def get_summary(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific summary by ID.
    Students can only access summaries for published courses.
    """
    summary = summary_crud.get_summary(db, summary_id=summary_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )

    # Check course access for students
    course = course_crud.get_course(db, course_id=summary.course_id)
    if current_user.role.value == "student" and (not course or course.status != CourseStatus.PUBLISHED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to unpublished course"
        )

    return summary


@router.post("", response_model=Summary, status_code=status.HTTP_201_CREATED)
def create_summary(
    summary: SummaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Create or update summary for a course (methodist only).
    If summary already exists for the course, it will be updated.
    """
    # Check if course exists
    course = course_crud.get_course(db, course_id=summary.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create summary for this course"
        )

    return summary_crud.create_summary(
        db=db,
        course_id=summary.course_id,
        content=summary.content
    )


@router.patch("/{summary_id}", response_model=Summary)
def update_summary(
    summary_id: int,
    summary_update: SummaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Update summary content (methodist only).
    Only the course creator can update the summary.
    """
    summary = summary_crud.get_summary(db, summary_id=summary_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )

    # Check if the current user is the creator of the course
    course = course_crud.get_course(db, course_id=summary.course_id)
    if not course or course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this summary"
        )

    updated_summary = summary_crud.update_summary(
        db=db,
        summary_id=summary_id,
        content=summary_update.content
    )

    if not updated_summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update summary"
        )

    return updated_summary


@router.delete("/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_summary(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Delete summary (methodist only).
    Only the course creator can delete the summary.
    """
    summary = summary_crud.get_summary(db, summary_id=summary_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )

    # Check if the current user is the creator of the course
    course = course_crud.get_course(db, course_id=summary.course_id)
    if course and course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this summary"
        )

    success = summary_crud.delete_summary(db, summary_id=summary_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete summary"
        )

    return None
