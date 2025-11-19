from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.test_result import TestResult, TestResultDetailed, DetailedAnswer, TestResultWithRelations
from app.crud import test_result as test_result_crud
from app.crud import test as test_crud
from app.crud import course as course_crud
from app.crud import user as user_crud
from app.services.auth_service import get_current_methodist, get_current_student
from app.models.user import User
import csv
import io

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=List[TestResultWithRelations])
def get_results(
    skip: int = 0,
    limit: int = 100,
    course_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Get all test results (methodist only).
    Returns complete information including student answers and scores.

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - course_id: Optional filter to get results only for a specific course
    """
    results = test_result_crud.get_test_results(db, skip=skip, limit=limit, course_id=course_id)
    return results


@router.get("/export")
def export_results(
    course_id: int = None,
    delimiter: str = ';',
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Export test results to CSV (methodist only).

    Query parameters:
    - course_id: Optional filter to export results only for a specific course
    - delimiter: CSV delimiter (default: ';' for Excel compatibility in CIS regions, can use ',' for US)

    CSV columns:
    - Result ID
    - Student Name
    - Student Email
    - Course Title
    - Test ID
    - Score
    - Total Questions
    - Percentage
    - Passed
    - Submitted At
    """
    # Get results (optionally filtered by course_id)
    results = test_result_crud.get_test_results(db, skip=0, limit=10000, course_id=course_id)

    # Create CSV in memory with UTF-8 BOM for Excel compatibility
    output = io.StringIO()
    # Write BOM for UTF-8 (important for Excel to recognize UTF-8 encoding)
    output.write('\ufeff')

    # Use specified delimiter (semicolon by default for CIS/European Excel)
    writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

    # Write header
    writer.writerow([
        "Result ID",
        "Student Name",
        "Student Email",
        "Course Title",
        "Test ID",
        "Score",
        "Total Questions",
        "Percentage",
        "Passed",
        "Submitted At"
    ])

    # Write data rows
    for result in results:
        # Use eager loaded relationships instead of additional queries
        student = result.student
        test = result.test
        course = course_crud.get_course(db, course_id=test.course_id) if test else None

        # Calculate percentage and pass status
        percentage = (result.score / result.total_questions * 100) if result.total_questions > 0 else 0
        passed = "Yes" if percentage >= 60.0 else "No"

        writer.writerow([
            result.id,
            student.full_name if student else "Unknown",
            student.email if student else "Unknown",
            course.title if course else "Unknown",
            result.test_id,
            result.score,
            result.total_questions,
            f"{percentage:.2f}",
            passed,
            result.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    # Prepare response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="test_results.csv"'
        }
    )


# ==================== Student Endpoints ====================


@router.get("/my", response_model=List[TestResultWithRelations])
def get_my_results(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Get all test results for the current student with full test and student information.
    Students can only see their own results.
    Includes eager loaded test and student objects for display on frontend.
    """
    results = test_result_crud.get_test_results_by_student(
        db, student_id=current_user.id, skip=skip, limit=limit
    )
    return results


@router.get("/my/course/{course_id}", response_model=List[TestResultDetailed])
def get_my_results_by_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Get all test results for the current student for a specific course.
    Returns detailed information including:
    - All questions with their text and options
    - Student's selected answers
    - Correct answers
    - Whether each answer was correct

    This allows the frontend to show a detailed breakdown of the test results.
    """
    # Check if course exists
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Get results for this student and course
    results = test_result_crud.get_test_results_by_student_and_course(
        db=db,
        student_id=current_user.id,
        course_id=course_id
    )

    # Enrich results with full question details
    detailed_results = []
    for result in results:
        # Get the test to access questions
        test = test_crud.get_test(db, test_id=result.test_id)
        if not test:
            continue

        # Build detailed answers with full question information
        detailed_answers = []
        for answer in result.answers:
            question_id = answer.get("question_id")
            if question_id < len(test.questions):
                question = test.questions[question_id]
                detailed_answer = DetailedAnswer(
                    question_id=question_id,
                    question=question["question"],
                    options=question["options"],
                    selected_answer=answer.get("selected_answer"),
                    correct_answer=question["correct_answer"],
                    is_correct=answer.get("is_correct", False)
                )
                detailed_answers.append(detailed_answer)

        # Calculate percentage and pass status
        percentage = (result.score / result.total_questions * 100) if result.total_questions > 0 else 0
        passed = percentage >= 60.0

        # Create detailed result
        detailed_result = TestResultDetailed(
            id=result.id,
            test_id=result.test_id,
            student_id=result.student_id,
            answers=detailed_answers,
            score=result.score,
            total_questions=result.total_questions,
            submitted_at=result.submitted_at,
            percentage=percentage,
            passed=passed
        )
        detailed_results.append(detailed_result)

    return detailed_results
