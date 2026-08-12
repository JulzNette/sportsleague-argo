import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class Division(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_divisions"
    __table_args__ = (
        UniqueConstraint("organization_id", "season_id", "name", name="uq_sportsleague_divisions_org_season_name"),
    )

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_teams: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    # Active | Archived

    season: Mapped["Season"] = relationship(back_populates="divisions")
    teams: Mapped[list["Team"]] = relationship(back_populates="division", cascade="all, delete-orphan")
