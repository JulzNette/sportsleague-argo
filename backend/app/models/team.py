import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class Team(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_teams"
    __table_args__ = (
        UniqueConstraint("organization_id", "division_id", "name", name="uq_sportsleague_teams_org_division_name"),
    )

    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    coach_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    # Active | Disqualified | Withdrawn

    division: Mapped["Division"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team", cascade="all, delete-orphan")
