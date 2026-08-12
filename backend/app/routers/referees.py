import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.referee import Referee
from app.schemas.referee import RefereeCreate, RefereeOut, RefereeUpdate
from app.services import crud

router = APIRouter(prefix="/referees", tags=["Referees"])


@router.get("", response_model=list[RefereeOut], summary="List Referees")
def list_referees(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("referee.manage")),
):
    return crud.list_scoped(db, Referee, organization_id=user.organization_id)


@router.get("/{referee_id}", response_model=RefereeOut, summary="Get Referee")
def get_referee(
    referee_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("referee.manage")),
):
    return crud.get_scoped_or_404(db, Referee, organization_id=user.organization_id, record_id=referee_id)


@router.post("", response_model=RefereeOut, status_code=201, summary="Create Referee")
def create_referee(
    payload: RefereeCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("referee.manage")),
):
    return crud.create_scoped(
        db, Referee, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{referee_id}", response_model=RefereeOut, summary="Update Referee")
def update_referee(
    referee_id: uuid.UUID,
    payload: RefereeUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("referee.manage")),
):
    obj = crud.get_scoped_or_404(db, Referee, organization_id=user.organization_id, record_id=referee_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))
