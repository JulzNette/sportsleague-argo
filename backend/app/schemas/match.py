import uuid
from datetime import date, time
from pydantic import BaseModel, Field, model_validator
from app.schemas.common import AuditFieldsOut
from app.schemas.result import MatchResultOut

_STATUS = "^(Scheduled|In Progress|Completed|Postponed|Cancelled|Forfeited)$"
_TYPE = "^(Regular|Playoff)$"


class MatchBase(BaseModel):
    season_id: uuid.UUID
    division_id: uuid.UUID
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    referee_id: uuid.UUID | None = None
    scheduled_date: date
    scheduled_time: time
    venue: str = Field(min_length=1, max_length=255)
    round_number: int = Field(default=0, ge=0)
    match_type: str = Field(default="Regular", pattern=_TYPE)

    @model_validator(mode="after")
    def _distinct_teams(self):
        if self.home_team_id == self.away_team_id:
            raise ValueError("home_team_id and away_team_id must be different teams")
        return self


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    referee_id: uuid.UUID | None = None
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    venue: str | None = Field(default=None, min_length=1, max_length=255)
    round_number: int | None = Field(default=None, ge=0)
    match_type: str | None = Field(default=None, pattern=_TYPE)


class MatchStatusUpdate(BaseModel):
    status: str = Field(pattern=_STATUS)


class MatchOut(MatchBase, AuditFieldsOut):
    status: str
    result: MatchResultOut | None = None
