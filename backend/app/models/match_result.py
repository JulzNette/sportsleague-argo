import uuid
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class MatchResult(OrgAuditMixin, Base):
    """
    One row per match (1:1). Scores are the only source of truth; standings
    are always computed from these rows on read, never stored (see
    app/services/standings.py) per the "never store derived values" rule.
    """
    __tablename__ = "sportsleague_match_results"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_matches.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    home_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Live game-clock state used by the Scoring page and the public scoreboard.
    period: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Normal")
    # Normal | Draw | Forfeit
    forfeit_winner_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_teams.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # submitted_by is redundant with created_by but kept as a distinct named
    # business field (e.g. the referee who phoned it in vs. the admin who typed
    # it into the system) - still a loose UUID, no FK to users.
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="result")
