import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.coach import Coach
from app.models.team import Team
from app.schemas.coach import CoachCreate, CoachOut, CoachUpdate
from app.services import crud

router = APIRouter(prefix="/coaches", tags=["Coaches"])


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
    coaches = crud.list_scoped(db, Coach, organization_id=user.organization_id, team_id=team_id)
    names = _team_names(db, [c.id for c in coaches])
    return [_to_out(c, names.get(c.id, "")) for c in coaches]


@router.get("/{coach_id}", response_model=CoachOut, summary="Get Coach")
def get_coach(
    coach_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("coach.view")),
):
    coach = crud.get_scoped_or_404(db, Coach, organization_id=user.organization_id, record_id=coach_id)
    names = _team_names(db, [coach.id])
    return _to_out(coach, names.get(coach.id, ""))


@router.post("", response_model=CoachOut, status_code=201, summary="Create Coach")
def create_coach(
    payload: CoachCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("coach.manage")),
):
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
    user: CurrentUser = Depends(require_permission("coach.manage")),
):
    obj = crud.get_scoped_or_404(db, Coach, organization_id=user.organization_id, record_id=coach_id)
    update = crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))
    return _to_out(update)


@router.delete("/{coach_id}", status_code=204, summary="Delete Coach")
def delete_coach(
    coach_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("coach.manage")),
):
    obj = crud.get_scoped_or_404(db, Coach, organization_id=user.organization_id, record_id=coach_id)
    crud.delete_scoped(db, obj)
