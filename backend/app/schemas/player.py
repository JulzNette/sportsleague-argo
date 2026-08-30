import uuid
from datetime import date
from pydantic import BaseModel, Field, EmailStr
from app.schemas.common import AuditFieldsOut

_STATUS = "^(Active|Inactive|Suspended)$"


class PlayerBase(BaseModel):
    team_id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date | None = None
    position: str | None = Field(default=None, max_length=100)
    jersey_number: str = Field(min_length=1, max_length=10)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str = Field(default="Active", pattern=_STATUS)


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    team_id: uuid.UUID | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    position: str | None = Field(default=None, max_length=100)
    jersey_number: str | None = Field(default=None, min_length=1, max_length=10)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, pattern=_STATUS)


class PlayerOut(PlayerBase, AuditFieldsOut):
    pass


class PlayerAccountCreate(BaseModel):
    """Credential set for a player's login. The account is created with the
    Player role so they can only view (standings, schedule, their stats)."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PlayerAccountOut(BaseModel):
    player_id: uuid.UUID
    email: str
    full_name: str
    role: str
