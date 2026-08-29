import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, OrgAuditMixin


class Coach(OrgAuditMixin, Base):
    """A coaching staff record for a team. Each team has one head coach row;
    the unique constraint keeps the org-team pairing to a single record."""
    __tablename__ = "sportsleague_coaches"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "team_id", name="uq_sportsleague_coaches_org_team",
        ),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_teams.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="Head Coach")
    # Head Coach | Assistant Coach
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    credentials: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    # Active | Inactive
