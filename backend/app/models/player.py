import uuid
from datetime import date
from sqlalchemy import String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class Player(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_players"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "team_id", "jersey_number",
            name="uq_sportsleague_players_org_team_jersey",
        ),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jersey_number: Mapped[str] = mapped_column(String(10), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    # Active | Inactive | Suspended

    team: Mapped["Team"] = relationship(back_populates="players")
