import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class FeeConfigOut(ORMBase):
    amount: float | None = None
    configured: bool = False


class FeeConfigUpdate(BaseModel):
    amount: float | None = Field(default=None, ge=0, description="Set to null/omit to unset the default fee")


class FoulLimitUpdate(BaseModel):
    foul_limit: int = Field(ge=1, le=20)


class ContentUpdate(BaseModel):
    key: str = Field(description="pricing_content or rewards_content")
    items: list[dict] = []


class DivisionFeeIn(BaseModel):
    division_id: uuid.UUID
    registration_fee: float = Field(ge=0)


class DivisionFeeOut(ORMBase):
    division_id: uuid.UUID
    registration_fee: float
    created_at: datetime
    updated_at: datetime


class PublicSettingsOut(BaseModel):
    registration_fee: float | None = None
    pricing: list[dict] = []
    rewards: list[dict] = []
    foul_limit: int = 5


class AdminSettingsOut(PublicSettingsOut):
    configured_fee: bool = False
    division_fees: list[DivisionFeeOut] = []
