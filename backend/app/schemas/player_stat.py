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
