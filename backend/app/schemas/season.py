import uuid
from datetime import date
from pydantic import BaseModel, Field, model_validator
from app.schemas.common import AuditFieldsOut

_STATUS = "^(Draft|Active|Completed|Cancelled)$"
_FORMAT = "^(Round Robin|Single Elimination|Custom)$"


class SeasonBase(BaseModel):
    league_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    format: str = Field(default="Round Robin", pattern=_FORMAT)
    status: str = Field(default="Draft", pattern=_STATUS)

    @model_validator(mode="after")
    def _check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    format: str | None = Field(default=None, pattern=_FORMAT)
    status: str | None = Field(default=None, pattern=_STATUS)


class SeasonOut(SeasonBase, AuditFieldsOut):
    pass
