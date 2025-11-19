from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


# Base schema
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole


# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)


# Schema for updating a user
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=72)


# Schema for user in responses
class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Schema for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72)


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
