import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AuditFieldsOut


class NotificationOut(AuditFieldsOut):
    user_id: uuid.UUID
    type: str
    title: str
    message: str | None
    registration_id: uuid.UUID | None
    is_read: bool
    read_at: datetime | None


class UnreadCountOut(BaseModel):
    count: int
