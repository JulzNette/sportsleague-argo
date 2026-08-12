"""
Submitting a result is a workflow action, not a plain CRUD create: it also
drives the match's status forward (Scheduled/In Progress -> Completed, or
-> Forfeited for a forfeit), matching the STATUS_TRANSITIONS_MATCH state
machine from the prototype.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.core.state_machines import MATCH_STATUS_TRANSITIONS, is_valid_transition
from app.models.match import Match
from app.models.match_result import MatchResult
from app.schemas.result import MatchResultCreate, MatchResultOut, MatchResultUpdate
from app.services import crud

router = APIRouter(prefix="/matches/{match_id}/result", tags=["Results"])


@router.get("", response_model=MatchResultOut, summary="Get Result")
def get_result(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("result.view")),
):
    crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    result = db.query(MatchResult).filter(
        MatchResult.organization_id == user.organization_id, MatchResult.match_id == match_id
    ).one_or_none()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No result recorded for this match yet")
    return result


@router.post("", response_model=MatchResultOut, status_code=201, summary="Submit Result")
def submit_result(
    match_id: uuid.UUID,
    payload: MatchResultCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("result.submit")),
):
    match = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)

    existing = db.query(MatchResult).filter(
        MatchResult.organization_id == user.organization_id, MatchResult.match_id == match_id
    ).one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A result already exists for this match - use PATCH to correct it.",
        )

    target_status = "Forfeited" if payload.result_type == "Forfeit" else "Completed"
    if not is_valid_transition(MATCH_STATUS_TRANSITIONS, match.status, target_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit a result for a match in '{match.status}' status.",
        )

    data = payload.model_dump()
    data["match_id"] = match_id
    data["submitted_by"] = user.id
    result = crud.create_scoped(
        db, MatchResult, organization_id=user.organization_id, user_id=user.id, data=data
    )
    match.status = target_status
    match.updated_by = user.id
    db.commit()
    db.refresh(result)
    return result


@router.patch("", response_model=MatchResultOut, summary="Correct Result")
def correct_result(
    match_id: uuid.UUID,
    payload: MatchResultUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("result.update")),
):
    crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    result = db.query(MatchResult).filter(
        MatchResult.organization_id == user.organization_id, MatchResult.match_id == match_id
    ).one_or_none()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No result recorded for this match yet")
    return crud.update_scoped(db, result, user_id=user.id, data=payload.model_dump())
