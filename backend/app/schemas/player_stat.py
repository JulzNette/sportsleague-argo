import uuid
from pydantic import BaseModel, Field


class PlayerStatLine(BaseModel):
    """One player's line for a match - scores are sport-agnostic and default to 0."""
    player_id: uuid.UUID
    points: int = Field(default=0, ge=0, le=10000)
    assists: int = Field(default=0, ge=0, le=10000)
    fouls: int = Field(default=0, ge=0, le=10000)
    rebounds: int = Field(default=0, ge=0, le=10000)
    steals: int = Field(default=0, ge=0, le=10000)


class PlayerStatsSubmit(BaseModel):
    """Replaces the full set of player stats for a match."""
    lines: list[PlayerStatLine] = Field(min_length=1, max_length=100)


class PlayerStatOut(PlayerStatLine):
    match_id: uuid.UUID
    team_id: uuid.UUID
    player_name: str
    team_name: str


class LiveStatUpdateIn(BaseModel):
    """Live scoring grid update: add points and/or a foul to one player for a
    match that is underway. Deltas so repeated button taps accumulate."""
    player_id: uuid.UUID
    points: int = Field(default=0, ge=0, le=100)
    fouls: int = Field(default=0, ge=0, le=100)


class FoulLimitIn(BaseModel):
    """Per-league foul limit for 'fouls out' (defaults to 5). Stored so the
    same limit is used across all matches in the org unless overridden."""
    foul_limit: int = Field(default=5, ge=1, le=20)


class LiveStatOut(PlayerStatOut):
    """PlayerStatOut plus live-scoring extras: whether this player has fouled
    out (fouls >= foul_limit) and the current foul limit."""
    fouls_out: bool
    foul_limit: int


class PlayerAggregateOut(BaseModel):
    """Aggregated per-player totals across completed matches (computed live)."""
    rank: int
    player_id: uuid.UUID
    player_name: str
    team_id: uuid.UUID
    team_name: str
    games_played: int
    points: int
    assists: int
    fouls: int
    rebounds: int
    steals: int
