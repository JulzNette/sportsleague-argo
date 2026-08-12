import uuid
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import AuditFieldsOut

_STATUS = "^(Active|Disqualified|Withdrawn)$"


class TeamBase(BaseModel):
    division_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    coach_name: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str = Field(default="Active", pattern=_STATUS)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    coach_name: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, pattern=_STATUS)


class TeamOut(TeamBase, AuditFieldsOut):
    pass
