"""
League registration workflow: a team applies to join a division by submitting
a registration (team info + roster + documents). An approved registration is
materialized into a Team and its Players; a rejected one stays on file with a
review comment. Until then everything lives in the registration tables.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import String, Date, Text, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, OrgAuditMixin


class Registration(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_registrations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "division_id", "team_name",
            name="uq_sportsleague_registrations_org_division_team",
        ),
    )

    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    coach_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending")
    # Pending | Approved | Rejected
    registration_fee: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Pending | Paid
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    division: Mapped["Division"] = relationship(back_populates="registrations")
    players: Mapped[list["RegistrationPlayer"]] = relationship(
        back_populates="registration", cascade="all, delete-orphan",
    )
    documents: Mapped[list["RegistrationDocument"]] = relationship(
        back_populates="registration", cascade="all, delete-orphan",
    )


class RegistrationPlayer(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_registration_players"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "registration_id", "jersey_number",
            name="uq_sportsleague_reg_players_reg_jersey",
        ),
    )

    registration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_registrations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jersey_number: Mapped[str] = mapped_column(String(10), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    registration: Mapped["Registration"] = relationship(back_populates="players")


class RegistrationDocument(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_registration_documents"

    registration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_registrations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # NULL = document applies to the whole team; otherwise a player's name.
    player_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    registration: Mapped["Registration"] = relationship(back_populates="documents")
