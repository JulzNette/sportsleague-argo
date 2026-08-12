import uuid
from pydantic import BaseModel


class StandingRow(BaseModel):
    """
    Computed on every request from sportsleague_matches + sportsleague_match_results.
    Never persisted - see app/services/standings.py.
    """
    team_id: uuid.UUID
    team_name: str
    matches_played: int
    wins: int
    losses: int
    draws: int
    points: int
