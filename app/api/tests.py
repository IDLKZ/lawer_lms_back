from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.test import TestForStudent, TestSubmit, QuestionForStudent, Test, TestCreate, TestUpdate
from app.schemas.test_result import TestSubmitResponse
from app.crud import test as test_crud
from app.crud import test_result as test_result_crud
from app.crud import course as course_crud
from app.services.auth_service import get_current_student, get_current_methodist, get_current_user
from app.models.user import User
from app.models.course import CourseStatus

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("", response_model=List[TestForStudent])
def get_tests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Get list of available tests (student only).
    Only shows tests for published courses.
    Questions are returned WITHOUT correct answers.
    """
    # Get all published courses
    published_courses = course_crud.get_courses(
        db, skip=skip, limit=limit, status=CourseStatus.PUBLISHED
    )

    # Get tests for these courses
    tests = []
    for course in published_courses:
        test = test_crud.get_test_by_course(db, course_id=course.id)
        if test:
            # Create test response without correct answers
            test_for_student = TestForStudent(
                id=test.id,
                course_id=test.course_id,
                created_at=test.created_at,
                questions=[
                    QuestionForStudent(
                        id=idx,
                        question=q["question"],
                        options=q["options"]
                    )
                    for idx, q in enumerate(test.questions)
                ]
            )
            tests.append(test_for_student)

    return tests


@router.get("/course/{course_id}", response_model=TestForStudent)
def get_test_by_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Get test for a specific course (student only).
    Returns questions WITHOUT correct answers.
    Only accessible for published courses.
    """
    # Check if the course is published
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    if course.status != CourseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test not available for unpublished course"
        )

    # Get test for the course
    test = test_crud.get_test_by_course(db, course_id=course_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found for this course"
        )

    # Return test without correct answers
    test_for_student = TestForStudent(
        id=test.id,
        course_id=test.course_id,
        created_at=test.created_at,
        questions=[
            QuestionForStudent(
                id=idx,
                question=q["question"],
                options=q["options"]
            )
            for idx, q in enumerate(test.questions)
        ]
    )

    return test_for_student


@router.get("/{test_id}", response_model=TestForStudent)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Get test questions (student only).
    Returns questions WITHOUT correct answers.
    Only accessible for published courses.
    """
    test = test_crud.get_test(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    # Check if the course is published
    course = course_crud.get_course(db, course_id=test.course_id)
    if not course or course.status != CourseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test not available for unpublished course"
        )

    # Return test without correct answers
    test_for_student = TestForStudent(
        id=test.id,
        course_id=test.course_id,
        created_at=test.created_at,
        questions=[
            QuestionForStudent(
                id=idx,
                question=q["question"],
                options=q["options"]
            )
            for idx, q in enumerate(test.questions)
        ]
    )

    return test_for_student


@router.post("/{test_id}/submit", response_model=TestSubmitResponse)
def submit_test(
    test_id: int,
    submission: TestSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Submit test answers (student only).

    This endpoint:
    1. Receives student's answers
    2. Calculates the score by comparing with correct answers (on backend!)
    3. Saves the result to database
    4. Returns score and pass/fail status

    IMPORTANT: Correct answers are NEVER sent to the frontend.
    All scoring is done on the backend.
    """
    # Get the test
    test = test_crud.get_test(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    # Check if the course is published
    course = course_crud.get_course(db, course_id=test.course_id)
    if not course or course.status != CourseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot submit test for unpublished course"
        )

    # Calculate score and prepare answers with is_correct flag
    total_questions = len(test.questions)
    correct_answers = 0

    # Convert answers to a dict for easier lookup
    answer_dict = {ans.question_id: ans.selected_answer for ans in submission.answers}

    # Prepare answers with is_correct flag
    answers_with_correctness = []
    for ans in submission.answers:
        question = test.questions[ans.question_id] if ans.question_id < len(test.questions) else None
        is_correct = False

        if question and ans.selected_answer == question["correct_answer"]:
            is_correct = True
            correct_answers += 1

        # Add answer with is_correct flag
        answer_data = ans.model_dump()
        answer_data["is_correct"] = is_correct
        answers_with_correctness.append(answer_data)

    # Calculate percentage
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    # Determine if passed (60% or higher)
    passed = percentage >= 60.0

    # Save result to database (create new or update existing)
    test_result_crud.create_or_update_test_result(
        db=db,
        test_id=test_id,
        student_id=current_user.id,
        answers=answers_with_correctness,
        score=correct_answers,
        total_questions=total_questions
    )

    # Return response
    return TestSubmitResponse(
        score=correct_answers,
        total=total_questions,
        passed=passed,
        percentage=percentage
    )


# ==================== Methodist Endpoints ====================


@router.get("/all", response_model=List[Test])
def get_all_tests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Get list of all tests with correct answers (methodist only).
    This endpoint is for methodists to manage tests.
    """
    tests = test_crud.get_tests(db, skip=skip, limit=limit)
    return tests


@router.get("/course/{course_id}/full", response_model=Test)
def get_test_full_by_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Get test with correct answers for a specific course (methodist only).
    """
    # Check if course exists
    course = course_crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Get test
    test = test_crud.get_test_by_course(db, course_id=course_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found for this course"
        )

    return test


@router.get("/{test_id}/full", response_model=Test)
def get_test_full(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Get test with correct answers (methodist only).
    This endpoint returns the complete test including correct answers.
    """
    test = test_crud.get_test(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    return test


@router.post("/create", response_model=Test, status_code=status.HTTP_201_CREATED)
def create_test(
    test: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Create or update test for a course (methodist only).
    If test already exists for the course, it will be updated.

    Questions format: [{"question": "...", "options": ["answer1", "answer2", "answer3", "answer4"], "correct_answer": "answer1"}, ...]
    Note: correct_answer must be the actual answer text, not a letter.
    """
    # Check if course exists
    course = course_crud.get_course(db, course_id=test.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if the current user is the creator of the course
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create test for this course"
        )

    # Validate questions format
    for idx, q in enumerate(test.questions):
        if not q.options or len(q.options) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {idx} must have at least 2 options"
            )
        if q.correct_answer not in q.options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {idx}: correct_answer must be one of the options"
            )

    # Convert Question objects to dict for storage
    questions_dict = [q.model_dump() for q in test.questions]

    return test_crud.create_test(
        db=db,
        course_id=test.course_id,
        questions=questions_dict
    )


@router.patch("/{test_id}", response_model=Test)
def update_test(
    test_id: int,
    test_update: TestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Update test questions (methodist only).
    Only the course creator can update the test.
    """
    test = test_crud.get_test(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    # Check if the current user is the creator of the course
    course = course_crud.get_course(db, course_id=test.course_id)
    if not course or course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this test"
        )

    # Validate questions format
    for idx, q in enumerate(test_update.questions):
        if not q.options or len(q.options) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {idx} must have at least 2 options"
            )
        if q.correct_answer not in q.options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {idx}: correct_answer must be one of the options"
            )

    # Convert Question objects to dict for storage
    questions_dict = [q.model_dump() for q in test_update.questions]

    updated_test = test_crud.update_test(
        db=db,
        test_id=test_id,
        questions=questions_dict
    )

    if not updated_test:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update test"
        )

    return updated_test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_methodist)
):
    """
    Delete test (methodist only).
    Only the course creator can delete the test.
    """
    test = test_crud.get_test(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    # Check if the current user is the creator of the course
    course = course_crud.get_course(db, course_id=test.course_id)
    if course and course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this test"
        )

    success = test_crud.delete_test(db, test_id=test_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete test"
        )

    return None
