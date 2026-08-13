import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerOut, PlayerUpdate
from app.services import crud

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("", response_model=list[PlayerOut], summary="List Players")
def list_players(
    team_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.view")),
):
    return crud.list_scoped(db, Player, organization_id=user.organization_id, team_id=team_id)


@router.get("/archived", response_model=list[PlayerOut], summary="List Archived Players")
def list_archived_players(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.view")),
):
    return crud.list_archived_scoped(db, Player, organization_id=user.organization_id)


@router.get("/{player_id}", response_model=PlayerOut, summary="Get Player")
def get_player(
    player_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.view")),
):
    return crud.get_scoped_or_404(db, Player, organization_id=user.organization_id, record_id=player_id)


@router.post("", response_model=PlayerOut, status_code=201, summary="Create Player")
def create_player(
    # covers "team.manage_roster" intent from the prototype: creating a
    # player is how a roster gets built.
    payload: PlayerCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.create")),
):
    return crud.create_scoped(
        db, Player, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{player_id}", response_model=PlayerOut, summary="Update Player")
def update_player(
    player_id: uuid.UUID,
    payload: PlayerUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.update")),
):
    obj = crud.get_scoped_or_404(db, Player, organization_id=user.organization_id, record_id=player_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))


@router.delete("/{player_id}", status_code=204, summary="Delete Player")
def delete_player(
    player_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.delete")),
):
    obj = crud.get_scoped_or_404(db, Player, organization_id=user.organization_id, record_id=player_id)
    crud.delete_scoped(db, obj)


@router.post("/{player_id}/restore", response_model=PlayerOut, summary="Restore Player")
def restore_player(
    player_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.update")),
):
    obj = crud.get_scoped_or_404(
        db, Player, organization_id=user.organization_id, record_id=player_id, include_archived=True
    )
    return crud.restore_scoped(db, obj)


@router.delete("/{player_id}/purge", status_code=204, summary="Permanently Delete Player")
def purge_player(
    player_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.delete")),
):
    obj = crud.get_scoped_or_404(
        db, Player, organization_id=user.organization_id, record_id=player_id, include_archived=True
    )
    crud.purge_scoped(db, obj)
