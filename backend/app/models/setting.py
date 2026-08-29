"""
Org-scoped application settings and per-division registration-fee overrides.

`AppSetting` is a simple key/value store (one row per key per organization)
used to persist global configuration that an Administrator manages, such as
the default registration fee and the public Pricing / Rewards page content.

`DivisionFee` overrides the default registration fee for a single division, so
an Administrator can charge different amounts per league/season/division.
"""
import uuid

from sqlalchemy import ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, OrgAuditMixin


class AppSetting(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_app_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", "key", name="uq_sportsleague_app_settings_org_key"),
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    # JSON body; contents depend on the key (see app/services/settings.py).
    value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class DivisionFee(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_division_fees"
    __table_args__ = (
        UniqueConstraint("division_id", name="uq_sportsleague_division_fees_division"),
    )

    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    registration_fee: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    division: Mapped["Division"] = relationship()  # noqa: F821
