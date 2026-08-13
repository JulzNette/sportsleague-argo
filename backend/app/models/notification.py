"""
In-app notifications. Receipts are a plain denormalized queue scoped to the
same organization as everything else: one row per recipient, with a loose
user_id (the users table is owned by another module) and an optional loose
registration_id so a notification can deep-link into the registration it
refers to without a hard FK that would break if that row is ever purged.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, OrgAuditMixin


class Notification(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_notifications"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", "type", "registration_id",
            name="uq_sportsleague_notifications_user_type_registration",
        ),
    )

    # Loose UUID - the recipient is a users row owned by another module.
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    # registration.submitted | registration.approved | registration.rejected
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Loose UUID - points at sportsleague_registrations.id but survives purges.
    registration_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
