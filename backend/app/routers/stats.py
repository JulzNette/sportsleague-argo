"""
Read-only statistics: per-player aggregates and leaderboards. Everything is
computed live from captured match results / player stats - never stored.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.schemas.player_stat import PlayerAggregateOut
from app.services.player_stats import aggregate_player_stats

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/players", response_model=list[PlayerAggregateOut], summary="Player Statistics")
def get_player_stats(
    season_id: uuid.UUID | None = None,
    division_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player_stat.view")),
):
    """Per-player totals across completed matches, ranked by points scored."""
    return aggregate_player_stats(
        db, organization_id=user.organization_id,
        season_id=season_id, division_id=division_id,
    )
