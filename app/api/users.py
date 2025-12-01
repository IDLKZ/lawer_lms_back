from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import User
from app.crud import user as user_crud
from app.services.auth_service import get_current_methodist
from app.models.user import User as UserModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[User])
def get_users(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_methodist)
):
    """
    Get list of all users (methodist only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        List of User objects
    """
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_methodist)
):
    """
    Get a specific user by ID (methodist only).

    Args:
        user_id: ID of the user
        db: Database session
        current_user: Currently authenticated user (must be methodist)

    Returns:
        User object
    """
    user = user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
