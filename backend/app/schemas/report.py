import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import AuditFieldsOut

_TYPE = "^(Season Summary|Match Report|Team Statistics|Referee Activity)$"


class ReportCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(pattern=_TYPE)
    season_id: uuid.UUID | None = None
    division_id: uuid.UUID | None = None


class ReportOut(AuditFieldsOut):
    name: str
    type: str
    season_id: uuid.UUID | None
    division_id: uuid.UUID | None
    generated_by: uuid.UUID
