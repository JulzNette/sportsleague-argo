import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.schemas.standing import StandingRow
from app.services.standings import compute_standings

router = APIRouter(prefix="/standings", tags=["Standings"])


@router.get("", response_model=list[StandingRow], summary="Get Standings")
def get_standings(
    season_id: uuid.UUID,
    division_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("standing.view")),
):
    """Always computed live from completed matches - see app/services/standings.py."""
    return compute_standings(
        db, organization_id=user.organization_id, season_id=season_id, division_id=division_id
    )
