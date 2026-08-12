import uuid
from datetime import date
from sqlalchemy import String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class Season(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_seasons"
    __table_args__ = (
        UniqueConstraint("organization_id", "league_id", "name", name="uq_sportsleague_seasons_org_league_name"),
    )

    # Intra-module FK only (both tables belong to this module) - allowed by the contract.
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_leagues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False, default="Round Robin")
    # Round Robin | Single Elimination | Custom
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Draft")
    # Draft | Active | Completed | Cancelled

    league: Mapped["League"] = relationship(back_populates="seasons")
    divisions: Mapped[list["Division"]] = relationship(back_populates="season", cascade="all, delete-orphan")
