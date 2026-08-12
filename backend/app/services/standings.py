"""
Standings are ALWAYS computed here, from sportsleague_matches +
sportsleague_match_results, and never written to a table - per the Argo
contract's "never store derived/calculated values" rule. Every call to this
function re-derives the table from scratch, so it can never drift from the
underlying match results.

Points model (ported from the prototype): Win = 3, Draw = 1, Loss = 0.
A forfeit counts as a win for forfeit_winner_team_id and a loss for the
other team; it does not add to either team's scored points total.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_result import MatchResult
from app.models.team import Team

POINTS_WIN = 3
POINTS_DRAW = 1
POINTS_LOSS = 0


def compute_standings(db: Session, *, organization_id: uuid.UUID, season_id: uuid.UUID,
                       division_id: uuid.UUID | None = None) -> list[dict]:
    query = (
        select(Match, MatchResult)
        .join(MatchResult, MatchResult.match_id == Match.id)
        .where(
            Match.organization_id == organization_id,
            Match.season_id == season_id,
            Match.status == "Completed",
        )
    )
    if division_id is not None:
        query = query.where(Match.division_id == division_id)

    rows = db.execute(query).all()

    stats: dict[uuid.UUID, dict] = {}

    def bucket(team_id: uuid.UUID) -> dict:
        return stats.setdefault(
            team_id,
            {"matches_played": 0, "wins": 0, "losses": 0, "draws": 0, "points": 0},
        )

    for match, result in rows:
        home, away = bucket(match.home_team_id), bucket(match.away_team_id)
        home["matches_played"] += 1
        away["matches_played"] += 1

        if result.result_type == "Forfeit" and result.forfeit_winner_team_id is not None:
            winner_id = result.forfeit_winner_team_id
            loser_id = match.away_team_id if winner_id == match.home_team_id else match.home_team_id
            bucket(winner_id)["wins"] += 1
            bucket(winner_id)["points"] += POINTS_WIN
            bucket(loser_id)["losses"] += 1
            bucket(loser_id)["points"] += POINTS_LOSS
            continue

        if result.home_score == result.away_score:
            home["draws"] += 1
            away["draws"] += 1
            home["points"] += POINTS_DRAW
            away["points"] += POINTS_DRAW
        elif result.home_score > result.away_score:
            home["wins"] += 1
            home["points"] += POINTS_WIN
            away["losses"] += 1
            away["points"] += POINTS_LOSS
        else:
            away["wins"] += 1
            away["points"] += POINTS_WIN
            home["losses"] += 1
            home["points"] += POINTS_LOSS

    if not stats:
        return []

    team_names = {
        t.id: t.name
        for t in db.execute(
            select(Team).where(Team.organization_id == organization_id, Team.id.in_(stats.keys()))
        ).scalars()
    }

    table = [
        {"team_id": team_id, "team_name": team_names.get(team_id, "Unknown"), **s}
        for team_id, s in stats.items()
    ]
    table.sort(key=lambda r: (-r["points"], -r["wins"], r["team_name"]))
    return table
