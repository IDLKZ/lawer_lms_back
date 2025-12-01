from sqlalchemy.orm import Session
from app.models.case import Case, CaseStatus
from app.schemas.case import CaseCreate, CaseUpdate, CaseFromPDF
from typing import Optional
from sqlalchemy import desc

def get_case(db: Session, case_id: int):
    """Get a single case by ID"""
    return db.query(Case).filter(Case.id == case_id).first()


def get_cases(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CaseStatus] = None
):
    """Get all cases with optional filtering by status, ordered by creation date (newest first)"""
    query = db.query(Case)

    # 1. Фильтрация по статусу (если указан)
    if status:
        query = query.filter(Case.status == status)

    # 2. Сортировка по created_at в убывающем порядке (DESC)
    query = query.order_by(desc(Case.created_at))

    # 3. Применение пагинации и выполнение запроса
    return query.offset(skip).limit(limit).all()


def get_cases_by_creator(
    db: Session,
    creator_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Get all cases created by a specific user"""
    return db.query(Case).filter(
        Case.created_by == creator_id
    ).offset(skip).limit(limit).all()


def create_case(db: Session, case: CaseCreate, creator_id: Optional[int] = None):
    """Create a new case"""
    db_case = Case(
        title=case.title,
        description=case.description,
        cleaning_text=case.cleaning_text,
        created_by=creator_id,
        status=case.status if case.status else CaseStatus.DRAFT
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def create_case_from_pdf(
    db: Session,
    case_data: CaseFromPDF,
    creator_id: Optional[int] = None
):
    """Create a new case from processed PDF data"""
    db_case = Case(
        title=case_data.title,
        description=case_data.description,
        cleaning_text=case_data.cleaned_text,
        created_by=creator_id,
        status=case_data.status if case_data.status else CaseStatus.DRAFT
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def update_case(db: Session, case_id: int, case_update: CaseUpdate):
    """Update an existing case"""
    db_case = get_case(db, case_id)
    if not db_case:
        return None

    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_case, field, value)

    db.commit()
    db.refresh(db_case)
    return db_case


def publish_case(db: Session, case_id: int):
    """Publish a case (change status to PUBLISHED)"""
    db_case = get_case(db, case_id)
    if not db_case:
        return None

    db_case.status = CaseStatus.PUBLISHED
    db.commit()
    db.refresh(db_case)
    return db_case


def unpublish_case(db: Session, case_id: int):
    """Unpublish a case (change status back to DRAFT)"""
    db_case = get_case(db, case_id)
    if not db_case:
        return None

    db_case.status = CaseStatus.DRAFT
    db.commit()
    db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_id: int):
    """Delete a case"""
    db_case = get_case(db, case_id)
    if db_case:
        db.delete(db_case)
        db.commit()
        return True
    return False
