import uuid
from pydantic import BaseModel, Field
from app.schemas.common import AuditFieldsOut


class DivisionBase(BaseModel):
    season_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    max_teams: int = Field(default=8, ge=2, le=64)
    status: str = Field(default="Active", pattern="^(Active|Archived)$")


class DivisionCreate(DivisionBase):
    pass


class DivisionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    max_teams: int | None = Field(default=None, ge=2, le=64)
    status: str | None = Field(default=None, pattern="^(Active|Archived)$")


class DivisionOut(DivisionBase, AuditFieldsOut):
    pass
