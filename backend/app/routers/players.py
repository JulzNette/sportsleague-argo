import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.core.security import hash_password
from app.models.player import Player
from app.models.registration import Registration
from app.models.stub import User
from app.models.team import Team
from app.schemas.player import PlayerAccountCreate, PlayerAccountOut, PlayerCreate, PlayerOut, PlayerUpdate
from app.services import crud

router = APIRouter(prefix="/players", tags=["Players"])

TEAM_MANAGER = "Team Manager"


def _manager_team_ids(db: Session, user: CurrentUser):
    """Teams this Team Manager owns, derived from the approved registrations they
    submitted (created_by == their account) - the same ownership convention the
    registration workflow uses to scope a manager's view."""
    if user.role != TEAM_MANAGER:
        return None
    ids: set[uuid.UUID] = set()
    regs = db.query(Registration).filter(
        Registration.organization_id == user.organization_id,
        Registration.created_by == user.id,
        Registration.status == "Approved",
    ).all()
    for reg in regs:
        team = db.query(Team).filter(
            Team.organization_id == user.organization_id,
            Team.division_id == reg.division_id,
            Team.name == reg.team_name,
        ).first()
        if team is not None:
            ids.add(team.id)
    return ids


def _ensure_player_allowed(db: Session, user: CurrentUser, player: Player) -> None:
    own = _manager_team_ids(db, user)
    if own is not None and player.team_id not in own:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create logins for players on your own team.",
        )


def _login_allowed(db: Session, user: CurrentUser, player: Player) -> bool:
    """Whether the current user may create a login for this player. Admins can
    create for anyone; a Team Manager only for players on their own team."""
    own = _manager_team_ids(db, user)
    if own is None:
        return True
    return player.team_id in own


def _to_out(db: Session, user: CurrentUser, player: Player) -> PlayerOut:
    out = PlayerOut.model_validate(player)
    out.login_allowed = _login_allowed(db, user, player)
    return out


@router.get("", response_model=list[PlayerOut], summary="List Players")
def list_players(
    team_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.view")),
):
    players = crud.list_scoped(db, Player, organization_id=user.organization_id, team_id=team_id)
    own = _manager_team_ids(db, user)
    if own is not None:
        players = [p for p in players if p.team_id in own]
    return [_to_out(db, user, p) for p in players]


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
    obj = crud.get_scoped_or_404(db, Player, organization_id=user.organization_id, record_id=player_id)
    return _to_out(db, user, obj)


@router.post("", response_model=PlayerOut, status_code=201, summary="Create Player")
def create_player(
    # covers "team.manage_roster" intent from the prototype: creating a
    # player is how a roster gets built.
    payload: PlayerCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.create")),
):
    return _to_out(db, user, crud.create_scoped(
        db, Player, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    ))


@router.patch("/{player_id}", response_model=PlayerOut, summary="Update Player")
def update_player(
    player_id: uuid.UUID,
    payload: PlayerUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.update")),
):
    obj = crud.get_scoped_or_404(db, Player, organization_id=user.organization_id, record_id=player_id)
    return _to_out(db, user, crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True)))


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
    restored = crud.restore_scoped(db, obj)
    return _to_out(db, user, restored)


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


@router.post("/{player_id}/account", response_model=PlayerAccountOut, status_code=201, summary="Create a Player login account")
def create_player_account(
    player_id: uuid.UUID,
    payload: PlayerAccountCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player.login")),
):
    """Create a Player-role login for a roster member. The Team Manager does this
    for their own players (scoped), admins for anyone. The account can only view
    the league - it cannot manage anything."""
    player = crud.get_scoped_or_404(
        db, Player, organization_id=user.organization_id, record_id=player_id
    )
    _ensure_player_allowed(db, user, player)

    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    account = User(
        organization_id=user.organization_id,
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=player.full_name,
        contact_phone=player.contact_phone,
        role="Player",
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return PlayerAccountOut(
        player_id=player.id, email=account.email,
        full_name=account.full_name, role=account.role,
    )
