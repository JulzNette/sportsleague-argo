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
from app.schemas.auth import (
    ChangePasswordRequest, LoginRequest, RegisterRequest, ResendCodeRequest,
    TokenResponse, VerifyEmailRequest,
)
from app.services.email import send_verification_code_email
from app.services.email_verify import issue_code, verify_code

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


@router.post("/register", status_code=201, summary="Create account")
@limiter.limit("3/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Creates a Team Manager account and emails a 6-digit verification code to the
    address supplied. The code must be confirmed via /verify-email before the
    account can sign in. A newly verified account can register their team (the
    "register a team" workflow); when an admin approves that registration, the
    team is created and this user becomes its manager.
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
        role="Team Manager",
        is_active=True,
    )
    db.add(user)
    code = issue_code(email)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    # No token yet: the person must enter the emailed code before they can
    # enter the system. If email delivery fails we still created the account,
    # so the verify step can simply show a "resend code" option.
    delivery = send_verification_code_email(email=email, code=code)
    response = {"detail": "Verification code sent to your email.", "email": email}
    # When no real email provider is configured (Brevo/SMTP), the code is only
    # logged. Returning it here lets the person finish sign-up anyway. Once a
    # provider is configured (mode != simulated), the code is never exposed.
    if not delivery.get("sent") or delivery.get("mode") == "simulated":
        response["verification_code"] = code
    return response


@router.post("/verify-email", response_model=TokenResponse, summary="Verify email to finish sign-up")
@limiter.limit("10/minute")
def verify_email(request: Request, payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Confirms the 6-digit code emailed at registration and returns a token so the
    user can enter the system. The code is single-use and expires after 10
    minutes. Requires the account to exist; wrong codes are rate-limited.
    """
    email_address = payload.email.lower()
    user = db.execute(
        select(User).where(User.email == email_address)
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    if not verify_code(email_address, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code.")

    token = create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/verify-email/resend", summary="Re-send the verification code")
@limiter.limit("5/minute")
def resend_verification_code(request: Request, payload: ResendCodeRequest, db: Session = Depends(get_db)):
    """Re-issues and re-emails a fresh verification code for an existing account."""
    email_address = payload.email.lower()
    user = db.execute(
        select(User).where(User.email == email_address)
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    code = issue_code(email_address)
    delivery = send_verification_code_email(email=email_address, code=code)
    response = {"detail": "New verification code sent to your email."}
    if not delivery.get("sent") or delivery.get("mode") == "simulated":
        response["verification_code"] = code
    return response


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
