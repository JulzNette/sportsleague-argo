"""
Shared FastAPI dependencies: current user extraction from JWT, and a
require_permission() factory for RBAC-guarded routes.

CRITICAL: organization_id is ALWAYS taken from the verified JWT (current_user.organization_id),
never from a path/query/body param. This is what stops any request from ever
reading or writing another tenant's rows - see Settings page note in the
original prototype ("derived from your authenticated session token").
"""
import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.permissions import role_has_permission
from app.core.security import decode_access_token
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@dataclass
class CurrentUser:
    id: uuid.UUID
    organization_id: uuid.UUID
    role: str


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = decode_access_token(token)
        return CurrentUser(
            id=uuid.UUID(payload["sub"]),
            organization_id=uuid.UUID(payload["org"]),
            role=payload["role"],
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_permission(permission: str):
    """Returns a FastAPI dependency that 403s unless the caller's role holds `permission`."""

    def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not role_has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires the '{permission}' permission, "
                    f"which the '{current_user.role}' role does not hold."
                ),
            )
        return current_user

    return _checker


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db
