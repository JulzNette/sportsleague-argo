"""
Per-player performance statistics for a single match (points, assists,
fouls, rebounds, steals). Sport-agnostic - a league sets which of these
matter, and the rest just stay at 0. One row per player per match.

These are *captured* data (staff enter them when a result is recorded),
never derived, so storing them does not violate the "never store derived
values" rule - standings and aggregates are still computed on read.
"""
import uuid

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, OrgAuditMixin


class PlayerGameStat(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_player_game_stats"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "match_id", "player_id",
            name="uq_sportsleague_player_game_stats_match_player",
        ),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_matches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_players.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # Team the player was on for this match - always one of the match's two
    # teams, recorded so aggregation can attribute stats per team.
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sportsleague_teams.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fouls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rebounds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    steals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
