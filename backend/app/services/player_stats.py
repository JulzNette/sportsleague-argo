"""
Aggregated player statistics.

Always recomputed live from sportsleague_player_game_stats joined to the
completed matches they belong to - never stored (per the "never store
derived/calculated values" rule). Filters are optional and applied to the
underlying matches (season, division).
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.player import Player
from app.models.player_stat import PlayerGameStat
from app.models.team import Team

_STAT_KEYS = ("points", "assists", "fouls", "rebounds", "steals")


def aggregate_player_stats(db: Session, *, organization_id: uuid.UUID,
                           season_id: uuid.UUID | None = None,
                           division_id: uuid.UUID | None = None) -> list[dict]:
    query = (
        select(PlayerGameStat, Player.full_name, Team.name)
        .join(Match, Match.id == PlayerGameStat.match_id)
        .join(Player, Player.id == PlayerGameStat.player_id)
        .join(Team, Team.id == PlayerGameStat.team_id)
        .where(
            PlayerGameStat.organization_id == organization_id,
            PlayerGameStat.deleted_at.is_(None),
            Match.deleted_at.is_(None),
            Match.status.in_(["Completed", "Forfeited"]),
        )
    )
    if season_id is not None:
        query = query.where(Match.season_id == season_id)
    if division_id is not None:
        query = query.where(Match.division_id == division_id)

    rows = db.execute(query).all()

    agg: dict[uuid.UUID, dict] = {}
    for stat, player_name, team_name in rows:
        bucket = agg.setdefault(
            stat.player_id,
            {
                "player_id": stat.player_id,
                "player_name": player_name,
                "team_id": stat.team_id,
                "team_name": team_name,
                "games_played": 0,
                "points": 0, "assists": 0, "fouls": 0, "rebounds": 0, "steals": 0,
            },
        )
        bucket["games_played"] += 1
        for key in _STAT_KEYS:
            bucket[key] += getattr(stat, key)

    table = list(agg.values())
    table.sort(key=lambda r: (-r["points"], -r["games_played"], r["player_name"]))
    for rank, row in enumerate(table, start=1):
        row["rank"] = rank
    return table
