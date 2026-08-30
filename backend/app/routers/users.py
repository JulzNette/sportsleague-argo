"""
User Management (Superadmin).

Lets a Superadmin manage all accounts in their organization: view the list of
users, create new accounts, edit their details/role/active flag, reset a
password, and deactivate (soft-delete) an account.

All rows are scoped to the caller's organization_id taken from the verified
JWT - never trusted from the request body.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_permission
from app.core.permissions import ROLES
from app.core.security import hash_password
from app.db.session import get_db
from app.models.stub import User
from app.schemas.user import UserCreate, UserOut, UserResetPassword, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _get_user(db: Session, user_id: uuid.UUID, org_id: uuid.UUID) -> User:
    user = db.execute(select(User).where(User.id == user_id, User.organization_id == org_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.get("", response_model=list[UserOut], summary="List users")
def list_users(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_permission("user.view")),
):
    rows = db.execute(
        select(User).where(User.organization_id == current.organization_id).order_by(User.full_name)
    ).scalars().all()
    return rows


@router.post("", response_model=UserOut, status_code=201, summary="Create user")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_permission("user.create")),
):
    if payload.role not in ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unknown role '{payload.role}'.")
    email = payload.email.lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user = User(
        organization_id=current.organization_id,
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        contact_phone=payload.contact_phone,
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut, summary="Update user")
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_permission("user.update")),
):
    user = _get_user(db, user_id, current.organization_id)
    if user.id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot edit your own account here.")

    if payload.role is not None and payload.role not in ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unknown role '{payload.role}'.")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.contact_phone is not None:
        user.contact_phone = payload.contact_phone
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", status_code=204, summary="Reset a user's password")
def reset_password(
    user_id: uuid.UUID,
    payload: UserResetPassword,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_permission("user.reset_password")),
):
    user = _get_user(db, user_id, current.organization_id)
    user.hashed_password = hash_password(payload.password)
    db.commit()


@router.delete("/{user_id}", status_code=204, summary="Deactivate a user")
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_permission("user.delete")),
):
    user = _get_user(db, user_id, current.organization_id)
    if user.id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account.")
    user.is_active = False
    db.commit()


@router.delete("/{user_id}/purge", status_code=204, summary="Permanently delete a user")
def purge_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_permission("user.purge")),
):
    """
    Hard-deletes the account row so its email is freed up and can be used again
    for a new registration. This is permanent and cannot be undone. Only
    Superadmins can do this, and you cannot purge your own account.
    """
    user = _get_user(db, user_id, current.organization_id)
    if user.id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account.")
    db.delete(user)
    db.commit()
