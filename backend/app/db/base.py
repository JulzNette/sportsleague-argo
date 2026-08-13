"""
Declarative base plus shared mixins that every sportsleague_ business table uses,
per the Argo DB integration contract:

  - UUID primary keys (default=uuid.uuid4, never serial ints)
  - organization_id UUID FK -> organizations.id, ON DELETE CASCADE, NOT NULL, indexed
    (leads every unique constraint)
  - audit columns: created_at, updated_at, created_by, updated_by
    (created_by/updated_by are loose UUIDs - no FK to the users table)
  - no FK to any other module's tables
  - never store derived/calculated values (totals, balances, standings, etc.)
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrgAuditMixin:
    """Mixin providing id, organization_id, and audit columns for every business table."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    # Loose UUIDs deliberately - no FK to the users table (owned by another module).
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Soft-delete marker. NULL = active, set = archived. Lists hide archived rows;
    # /archived endpoints list them, /restore clears it, /purge hard-deletes.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
