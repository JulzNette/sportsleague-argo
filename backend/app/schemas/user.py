from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    contact_phone: str | None = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(min_length=1, max_length=64)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=32)
    role: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None


class UserResetPassword(BaseModel):
    password: str = Field(min_length=8, max_length=128)
