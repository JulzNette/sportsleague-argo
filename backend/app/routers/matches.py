import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.core.state_machines import MATCH_STATUS_TRANSITIONS, is_valid_transition
from app.models.match import Match
from app.schemas.match import MatchCreate, MatchOut, MatchStatusUpdate, MatchUpdate
from app.services import crud

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("", response_model=list[MatchOut], summary="List Matches")
def list_matches(
    season_id: uuid.UUID | None = None,
    division_id: uuid.UUID | None = None,
    status_: str | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.view")),
):
    return crud.list_scoped(
        db, Match, organization_id=user.organization_id,
        season_id=season_id, division_id=division_id, status=status_,
    )


@router.get("/archived", response_model=list[MatchOut], summary="List Archived Matches")
def list_archived_matches(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.view")),
):
    return crud.list_archived_scoped(db, Match, organization_id=user.organization_id)


@router.get("/{match_id}", response_model=MatchOut, summary="Get Match")
def get_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.view")),
):
    return crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)


@router.post("", response_model=MatchOut, status_code=201, summary="Create Match")
def schedule_match(
    payload: MatchCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.schedule")),
):
    return crud.create_scoped(
        db, Match, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{match_id}", response_model=MatchOut, summary="Update Match")
def update_match(
    match_id: uuid.UUID,
    payload: MatchUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))


@router.post("/{match_id}/assign-referee", response_model=MatchOut, summary="Assign Referee")
def assign_referee(
    match_id: uuid.UUID,
    referee_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("assignment.create")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    return crud.update_scoped(db, obj, user_id=user.id, data={"referee_id": referee_id})


@router.post("/{match_id}/status", response_model=MatchOut, summary="Update Match Status")
def transition_match_status(
    match_id: uuid.UUID,
    payload: MatchStatusUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    if not is_valid_transition(MATCH_STATUS_TRANSITIONS, obj.status, payload.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition match from '{obj.status}' to '{payload.status}'",
        )
    return crud.update_scoped(db, obj, user_id=user.id, data={"status": payload.status})


@router.delete("/{match_id}", status_code=204, summary="Delete Match")
def delete_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    crud.delete_scoped(db, obj)


@router.post("/{match_id}/restore", response_model=MatchOut, summary="Restore Match")
def restore_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(
        db, Match, organization_id=user.organization_id, record_id=match_id, include_archived=True
    )
    return crud.restore_scoped(db, obj)


@router.delete("/{match_id}/purge", status_code=204, summary="Permanently Delete Match")
def purge_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(
        db, Match, organization_id=user.organization_id, record_id=match_id, include_archived=True
    )
    crud.purge_scoped(db, obj)
