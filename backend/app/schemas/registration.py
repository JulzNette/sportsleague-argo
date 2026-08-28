import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import AuditFieldsOut

_STATUS = "^(Pending|Approved|Rejected)$"
_PAYMENT = "^(Pending|Paid)$"


class RegistrationPlayerIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date | None = None
    position: str | None = Field(default=None, max_length=100)
    jersey_number: str = Field(min_length=1, max_length=10)
    contact_phone: str | None = Field(default=None, max_length=32)


class RegistrationDocumentIn(BaseModel):
    # player_full_name == None means the document covers the whole team.
    player_full_name: str | None = Field(default=None, max_length=255)
    document_type: str = Field(min_length=1, max_length=255)
    file_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class RegistrationCreate(BaseModel):
    division_id: uuid.UUID
    team_name: str = Field(min_length=1, max_length=255)
    coach_name: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    registration_fee: float = Field(ge=0, description="Registration fee (amount typed by the registrant)")
    notes: str | None = None
    players: list[RegistrationPlayerIn] = Field(min_length=1)
    documents: list[RegistrationDocumentIn] = []


class RegistrationReview(BaseModel):
    status: str = Field(pattern="^(Approved|Rejected)$")
    review_comment: str | None = Field(default=None, max_length=2000)


class PaymentUpdate(BaseModel):
    payment_status: str = Field(pattern=_PAYMENT)


class RegistrationPlayerOut(AuditFieldsOut):
    full_name: str
    date_of_birth: date | None
    position: str | None
    jersey_number: str
    contact_phone: str | None


class RegistrationDocumentOut(AuditFieldsOut):
    player_full_name: str | None
    document_type: str
    file_name: str | None
    notes: str | None


class RegistrationOut(AuditFieldsOut):
    division_id: uuid.UUID
    team_name: str
    coach_name: str | None
    contact_email: EmailStr | None
    contact_phone: str | None
    manager_email: EmailStr | None = None
    registration_fee: float | None
    payment_status: str
    notes: str | None
    status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    review_comment: str | None
    players: list[RegistrationPlayerOut] = []
    documents: list[RegistrationDocumentOut] = []
