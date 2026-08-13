import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.division import Division
from app.schemas.division import DivisionCreate, DivisionOut, DivisionUpdate
from app.services import crud

router = APIRouter(prefix="/divisions", tags=["Divisions"])


@router.get("", response_model=list[DivisionOut], summary="List Divisions")
def list_divisions(
    season_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.view")),
):
    return crud.list_scoped(db, Division, organization_id=user.organization_id, season_id=season_id)


@router.get("/archived", response_model=list[DivisionOut], summary="List Archived Divisions")
def list_archived_divisions(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.view")),
):
    return crud.list_archived_scoped(db, Division, organization_id=user.organization_id)


@router.get("/{division_id}", response_model=DivisionOut, summary="Get Division")
def get_division(
    division_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.view")),
):
    return crud.get_scoped_or_404(db, Division, organization_id=user.organization_id, record_id=division_id)


@router.post("", response_model=DivisionOut, status_code=201, summary="Create Division")
def create_division(
    payload: DivisionCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.manage")),
):
    return crud.create_scoped(
        db, Division, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{division_id}", response_model=DivisionOut, summary="Update Division")
def update_division(
    division_id: uuid.UUID,
    payload: DivisionUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.manage")),
):
    obj = crud.get_scoped_or_404(db, Division, organization_id=user.organization_id, record_id=division_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))


@router.delete("/{division_id}", status_code=204, summary="Delete Division")
def delete_division(
    division_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.manage")),
):
    obj = crud.get_scoped_or_404(db, Division, organization_id=user.organization_id, record_id=division_id)
    crud.delete_scoped(db, obj)


@router.post("/{division_id}/restore", response_model=DivisionOut, summary="Restore Division")
def restore_division(
    division_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.manage")),
):
    obj = crud.get_scoped_or_404(
        db, Division, organization_id=user.organization_id, record_id=division_id, include_archived=True
    )
    return crud.restore_scoped(db, obj)


@router.delete("/{division_id}/purge", status_code=204, summary="Permanently Delete Division")
def purge_division(
    division_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("division.manage")),
):
    obj = crud.get_scoped_or_404(
        db, Division, organization_id=user.organization_id, record_id=division_id, include_archived=True
    )
    crud.purge_scoped(db, obj)
