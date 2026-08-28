"""
Auth: local-sandbox login plus self-service account creation.

- login: verifies credentials against the stub `users` table.
- register: anyone can create an account, but it is ALWAYS created with the
  read-only "Viewer" role - the role is hardcoded server-side and can never
  be chosen by the caller. Only a System Administrator can create/edit
  business data.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.stub import Organization, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Login")
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
@limiter.limit("10/minute")
def login_for_docs(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == form_data.username.lower())).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/register", response_model=TokenResponse, status_code=201, summary="Create account")
@limiter.limit("3/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Creates a read-only Viewer account. New accounts can view leagues, teams,
    matches and standings but cannot create, edit, or delete anything.
    """
    email = payload.email.lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    org = db.execute(select(Organization).limit(1)).scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No organization is configured for this deployment yet.",
        )

    user = User(
        organization_id=org.id,
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        contact_phone=payload.contact_phone,
        role="Viewer",
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    token = create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/change-password", status_code=204, summary="Change password")
@limiter.limit("5/minute")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Lets the logged-in user set a new password. The current password must be
    supplied and verified first. Only the account that owns the session token
    can be changed - there is no way to change another user's password here.
    """
    row = db.execute(select(User).where(User.id == user.id)).scalar_one_or_none()
    if row is None or not row.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    if not verify_password(payload.current_password, row.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

    row.hashed_password = hash_password(payload.new_password)
    db.commit()
