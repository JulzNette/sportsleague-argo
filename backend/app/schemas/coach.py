import uuid
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import AuditFieldsOut

_STATUS = "^(Active|Inactive)$"
_ROLE = "^(Head Coach|Assistant Coach)$"


class CoachBase(BaseModel):
    team_id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="Head Coach", pattern=_ROLE)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    credentials: str | None = Field(default=None, max_length=255)
    status: str = Field(default="Active", pattern=_STATUS)


class CoachCreate(CoachBase):
    pass


class CoachUpdate(BaseModel):
    team_id: uuid.UUID | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = Field(default=None, pattern=_ROLE)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    credentials: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, pattern=_STATUS)


class CoachOut(CoachBase, AuditFieldsOut):
    team_name: str = ""
