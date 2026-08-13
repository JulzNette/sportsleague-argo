import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.league import League
from app.schemas.league import LeagueCreate, LeagueOut, LeagueUpdate
from app.services import crud

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("", response_model=list[LeagueOut], summary="List Leagues")
def list_leagues(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.view")),
):
    return crud.list_scoped(db, League, organization_id=user.organization_id)


@router.get("/archived", response_model=list[LeagueOut], summary="List Archived Leagues")
def list_archived_leagues(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.view")),
):
    return crud.list_archived_scoped(db, League, organization_id=user.organization_id)


@router.get("/{league_id}", response_model=LeagueOut, summary="Get League")
def get_league(
    league_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.view")),
):
    return crud.get_scoped_or_404(db, League, organization_id=user.organization_id, record_id=league_id)


@router.post("", response_model=LeagueOut, status_code=201, summary="Create League")
def create_league(
    payload: LeagueCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.create")),
):
    return crud.create_scoped(
        db, League, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{league_id}", response_model=LeagueOut, summary="Update League")
def update_league(
    league_id: uuid.UUID,
    payload: LeagueUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.update")),
):
    obj = crud.get_scoped_or_404(db, League, organization_id=user.organization_id, record_id=league_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))


@router.delete("/{league_id}", status_code=204, summary="Delete League")
def delete_league(
    league_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.delete")),
):
    obj = crud.get_scoped_or_404(db, League, organization_id=user.organization_id, record_id=league_id)
    crud.delete_scoped(db, obj)


@router.post("/{league_id}/restore", response_model=LeagueOut, summary="Restore League")
def restore_league(
    league_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.update")),
):
    obj = crud.get_scoped_or_404(
        db, League, organization_id=user.organization_id, record_id=league_id, include_archived=True
    )
    return crud.restore_scoped(db, obj)


@router.delete("/{league_id}/purge", status_code=204, summary="Permanently Delete League")
def purge_league(
    league_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("league.delete")),
):
    obj = crud.get_scoped_or_404(
        db, League, organization_id=user.organization_id, record_id=league_id, include_archived=True
    )
    crud.purge_scoped(db, obj)
