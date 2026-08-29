import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.match import Match
from app.models.match_result import MatchResult
from app.schemas.result import MatchResultOut, ScoreUndo, ScoreUpdate

router = APIRouter(prefix="/matches/{match_id}/score", tags=["Scoring"])


@router.post("", response_model=MatchResultOut, status_code=200, summary="Update Live Score")
def update_live_score(
    match_id: uuid.UUID,
    payload: ScoreUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("result.update")),
):
    """Apply a live scoring update: add points to either team's running total and
    (optionally) advance the game clock. The result row is created on first use
    with zeros so a match can be scored live before a final result is submitted.

    Also flips a 'Scheduled' match to 'In Progress' so scoring a game surfaces it
    as live on the public landing page.
    """
    match = db.get(Match, match_id)
    if match is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Match not found")

    result = (
        db.query(MatchResult).filter(MatchResult.match_id == match.id).first()
    )
    if result is None:
        result = MatchResult(
            match_id=match.id,
            organization_id=match.organization_id,
            home_score=0,
            away_score=0,
            period=1,
            minutes=0,
            seconds=0,
            result_type="Normal",
            submitted_by=user.id,
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(result)

    result.home_score += payload.home_delta
    result.away_score += payload.away_delta
    if payload.period is not None:
        result.period = payload.period
    if payload.minutes is not None:
        result.minutes = payload.minutes
    if payload.seconds is not None:
        result.seconds = payload.seconds
    result.updated_by = user.id
    db.commit()
    db.refresh(result)

    if match.status == "Scheduled" and (payload.home_delta or payload.away_delta):
        match.status = "In Progress"
        db.commit()

    return result


@router.post("/undo", response_model=MatchResultOut, status_code=200, summary="Undo Points")
def undo_points(
    match_id: uuid.UUID,
    payload: ScoreUndo,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("result.update")),
):
    """Rewind a mistaken scoreboard entry: subtract `points` from one team's
    running total. The total is clamped at zero so it never goes negative.
    """
    from fastapi import HTTPException
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    result = (
        db.query(MatchResult).filter(MatchResult.match_id == match.id).first()
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No result yet to undo")

    if payload.side == "home":
        result.home_score = max(0, result.home_score - payload.points)
    else:
        result.away_score = max(0, result.away_score - payload.points)

    result.updated_by = user.id
    db.commit()
    db.refresh(result)
    return result
