from pydantic import BaseModel, Field
from app.schemas.common import AuditFieldsOut

_STATUS = "^(Active|Inactive|Suspended)$"


class RefereeBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    license_number: str = Field(min_length=1, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str = Field(default="Active", pattern=_STATUS)


class RefereeCreate(RefereeBase):
    pass


class RefereeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    license_number: str | None = Field(default=None, min_length=1, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, pattern=_STATUS)


class RefereeOut(RefereeBase, AuditFieldsOut):
    pass
