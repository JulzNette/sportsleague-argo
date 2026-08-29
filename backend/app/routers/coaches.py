import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, get_db_session, require_permission
from app.core.permissions import role_has_permission
from app.models.coach import Coach
from app.models.registration import Registration
from app.models.team import Team
from app.schemas.coach import CoachCreate, CoachOut, CoachUpdate
from app.services import crud

router = APIRouter(prefix="/coaches", tags=["Coaches"])

TEAM_MANAGER = "Team Manager"


def _require_coach_access(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin/manager roles manage any coach via coach.manage; a Team Manager is
    allowed in but can only touch the coach of their own team(s) - enforced per
    request by requiring the target team be one they registered."""
    if role_has_permission(current_user.role, "coach.manage") or current_user.role == TEAM_MANAGER:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to manage coaches.",
    )


def _manager_team_ids(db: Session, user: CurrentUser) -> set[uuid.UUID]:
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


def _ensure_allowed(db: Session, user: CurrentUser, team_id: uuid.UUID) -> None:
    own = _manager_team_ids(db, user)
    if own is not None and team_id not in own:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage the coach for your own team.",
        )


def _team_names(db: Session, coach_ids):
    names: dict[uuid.UUID, str] = {}
    if not coach_ids:
        return names
    rows = db.execute(
        select(Coach.id, Team.name)
        .join(Team, Team.id == Coach.team_id)
        .where(Coach.id.in_(coach_ids))
    ).all()
    for coach_id, team_name in rows:
        names[coach_id] = team_name
    return names


def _to_out(coach: Coach, team_name: str = "") -> CoachOut:
    return CoachOut(
        id=coach.id, organization_id=coach.organization_id,
        created_at=coach.created_at, updated_at=coach.updated_at,
        created_by=coach.created_by, updated_by=coach.updated_by,
        team_id=coach.team_id, team_name=team_name,
        full_name=coach.full_name, role=coach.role,
        email=coach.email, phone=coach.phone,
        credentials=coach.credentials, status=coach.status,
    )


@router.get("", response_model=list[CoachOut], summary="List Coaches")
def list_coaches(
    team_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("coach.view")),
):
    own = _manager_team_ids(db, user)
    coaches = crud.list_scoped(db, Coach, organization_id=user.organization_id, team_id=team_id)
    if own is not None:
        coaches = [c for c in coaches if c.team_id in own]
    names = _team_names(db, [c.id for c in coaches])
    return [_to_out(c, names.get(c.id, "")) for c in coaches]


@router.get("/{coach_id}", response_model=CoachOut, summary="Get Coach")
def get_coach(
    coach_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("coach.view")),
):
    coach = crud.get_scoped_or_404(db, Coach, organization_id=user.organization_id, record_id=coach_id)
    own = _manager_team_ids(db, user)
    if own is not None and coach.team_id not in own:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coach not found")
    names = _team_names(db, [coach.id])
    return _to_out(coach, names.get(coach.id, ""))


@router.post("", response_model=CoachOut, status_code=201, summary="Create Coach")
def create_coach(
    payload: CoachCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(_require_coach_access),
):
    _ensure_allowed(db, user, payload.team_id)
    coach = crud.create_scoped(
        db, Coach, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )
    team_name = db.execute(select(Team.name).where(Team.id == coach.team_id)).scalar_one_or_none() or ""
    return _to_out(coach, team_name)


@router.patch("/{coach_id}", response_model=CoachOut, summary="Update Coach")
def update_coach(
    coach_id: uuid.UUID,
    payload: CoachUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(_require_coach_access),
):
    obj = crud.get_scoped_or_404(db, Coach, organization_id=user.organization_id, record_id=coach_id)
    target_team = payload.team_id if payload.team_id is not None else obj.team_id
    _ensure_allowed(db, user, target_team)
    update = crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))
    return _to_out(update)


@router.delete("/{coach_id}", status_code=204, summary="Delete Coach")
def delete_coach(
    coach_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(_require_coach_access),
):
    obj = crud.get_scoped_or_404(db, Coach, organization_id=user.organization_id, record_id=coach_id)
    _ensure_allowed(db, user, obj.team_id)
    crud.delete_scoped(db, obj)
