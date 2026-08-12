"""
Local-sandbox login only: issues a JWT against the stub `users` table.
In the real Argo platform, authentication is owned by another module -
this router exists purely so the Sports League Management module can be
run and demoed standalone.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.stub import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse, summary="Login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)

@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def login_for_docs(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == form_data.username)).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)