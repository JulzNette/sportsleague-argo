import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate
from app.services import crud

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("", response_model=list[TeamOut])
def list_teams(
    division_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("team.view")),
):
    return crud.list_scoped(db, Team, organization_id=user.organization_id, division_id=division_id)


@router.get("/{team_id}", response_model=TeamOut)
def get_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("team.view")),
):
    return crud.get_scoped_or_404(db, Team, organization_id=user.organization_id, record_id=team_id)


@router.post("", response_model=TeamOut, status_code=201)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("team.create")),
):
    return crud.create_scoped(
        db, Team, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: uuid.UUID,
    payload: TeamUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("team.update")),
):
    obj = crud.get_scoped_or_404(db, Team, organization_id=user.organization_id, record_id=team_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("team.delete")),
):
    obj = crud.get_scoped_or_404(db, Team, organization_id=user.organization_id, record_id=team_id)
    crud.delete_scoped(db, obj)
