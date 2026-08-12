from pydantic import BaseModel, Field
from app.schemas.common import AuditFieldsOut


class LeagueBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sport_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    status: str = Field(default="Active", pattern="^(Active|Archived)$")


class LeagueCreate(LeagueBase):
    pass


class LeagueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sport_type: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(Active|Archived)$")


class LeagueOut(LeagueBase, AuditFieldsOut):
    pass
