import uuid
from pydantic import BaseModel, Field, model_validator
from app.schemas.common import AuditFieldsOut

_RESULT_TYPE = "^(Normal|Draw|Forfeit)$"


class MatchResultCreate(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    result_type: str = Field(default="Normal", pattern=_RESULT_TYPE)
    forfeit_winner_team_id: uuid.UUID | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_consistency(self):
        if self.result_type == "Draw" and self.home_score != self.away_score:
            raise ValueError("result_type 'Draw' requires home_score == away_score")
        if self.result_type == "Forfeit" and self.forfeit_winner_team_id is None:
            raise ValueError("result_type 'Forfeit' requires forfeit_winner_team_id")
        return self


class MatchResultUpdate(MatchResultCreate):
    pass


class MatchResultOut(AuditFieldsOut):
    match_id: uuid.UUID
    home_score: int
    away_score: int
    period: int
    minutes: int
    seconds: int
    result_type: str
    forfeit_winner_team_id: uuid.UUID | None
    notes: str | None
    submitted_by: uuid.UUID


class ScoreUpdate(BaseModel):
    """Live scoring update emitted by the Scoring page. Deltas are added to the
    running totals; clock fields overwrite the current game-clock state.
    """
    home_delta: int = Field(default=0, ge=0)
    away_delta: int = Field(default=0, ge=0)
    period: int | None = Field(default=None, ge=1, le=99)
    minutes: int | None = Field(default=None, ge=0, le=59)
    seconds: int | None = Field(default=None, ge=0, le=59)
