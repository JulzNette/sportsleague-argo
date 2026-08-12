import uuid
from datetime import date, time
from sqlalchemy import String, Date, Time, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class Match(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_matches"
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_sportsleague_matches_distinct_teams"),
    )

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    home_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    away_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_referees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Regular")
    # Regular | Playoff
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Scheduled")
    # Scheduled | In Progress | Completed | Postponed | Cancelled | Forfeited

    result: Mapped["MatchResult"] = relationship(back_populates="match", uselist=False, cascade="all, delete-orphan")
