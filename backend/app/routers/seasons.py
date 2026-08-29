import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.core.state_machines import SEASON_STATUS_TRANSITIONS, is_valid_transition
from app.models.league import League
from app.models.season import Season
from app.schemas.season import SeasonCreate, SeasonOut, SeasonUpdate
from app.services import crud

router = APIRouter(prefix="/seasons", tags=["Seasons"])


@router.get("", response_model=list[SeasonOut], summary="List Seasons")
def list_seasons(
    league_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.view")),
):
    # Only show seasons whose league still exists and is not archived; orphans of a
    # soft-deleted league are hidden so they cannot be picked in dropdowns.
    stmt = (
        select(Season)
        .join(League, League.id == Season.league_id)
        .where(Season.organization_id == user.organization_id)
        .where(Season.deleted_at.is_(None))
        .where(League.deleted_at.is_(None))
    )
    if league_id is not None:
        stmt = stmt.where(Season.league_id == league_id)
    stmt = stmt.order_by(Season.created_at.desc())
    return db.scalars(stmt).all()


@router.get("/archived", response_model=list[SeasonOut], summary="List Archived Seasons")
def list_archived_seasons(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.view")),
):
    return crud.list_archived_scoped(db, Season, organization_id=user.organization_id)


@router.get("/{season_id}", response_model=SeasonOut, summary="Get Season")
def get_season(
    season_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.view")),
):
    return crud.get_scoped_or_404(db, Season, organization_id=user.organization_id, record_id=season_id)


@router.post("", response_model=SeasonOut, status_code=201, summary="Create Season")
def create_season(
    payload: SeasonCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.create")),
):
    return crud.create_scoped(
        db, Season, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{season_id}", response_model=SeasonOut, summary="Update Season")
def update_season(
    season_id: uuid.UUID,
    payload: SeasonUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.update")),
):
    obj = crud.get_scoped_or_404(db, Season, organization_id=user.organization_id, record_id=season_id)
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and not is_valid_transition(SEASON_STATUS_TRANSITIONS, obj.status, data["status"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition season from '{obj.status}' to '{data['status']}'",
        )
    return crud.update_scoped(db, obj, user_id=user.id, data=data)


@router.delete("/{season_id}", status_code=204, summary="Delete Season")
def delete_season(
    season_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.update")),
):
    obj = crud.get_scoped_or_404(db, Season, organization_id=user.organization_id, record_id=season_id)
    crud.delete_scoped(db, obj)


@router.post("/{season_id}/restore", response_model=SeasonOut, summary="Restore Season")
def restore_season(
    season_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.update")),
):
    obj = crud.get_scoped_or_404(
        db, Season, organization_id=user.organization_id, record_id=season_id, include_archived=True
    )
    return crud.restore_scoped(db, obj)


@router.delete("/{season_id}/purge", status_code=204, summary="Permanently Delete Season")
def purge_season(
    season_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("season.update")),
):
    obj = crud.get_scoped_or_404(
        db, Season, organization_id=user.organization_id, record_id=season_id, include_archived=True
    )
    crud.purge_scoped(db, obj)
