"""Shared base classes for schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuditFieldsOut(ORMBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: uuid.UUID
