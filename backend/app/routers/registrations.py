import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.core.permissions import role_has_permission
from app.models.registration import Registration
from app.models.stub import User
from app.schemas.registration import (
    PaymentUpdate, RegistrationCreate, RegistrationOut, RegistrationReview,
)
from app.services import crud, registrations
from app.services.email import send_registration_email

router = APIRouter(prefix="/registrations", tags=["Registrations"])

_LOAD_OPTIONS = [
    selectinload(Registration.players),
    selectinload(Registration.documents),
]


def _fill_manager_email(db: Session, obj) -> None:
    """Expose the submitting Team Manager's account email + name on the response."""
    user = db.get(User, obj.created_by)
    obj.manager_email = user.email if user else None
    obj.manager_name = user.full_name if user else None


def _fill_manager_emails(db: Session, objects) -> None:
    for obj in objects:
        _fill_manager_email(db, obj)


@router.get("", response_model=list[RegistrationOut], summary="List Registrations")
def list_registrations(
    status: str | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("registration.view")),
):
    """
    Reviewers see every registration in the org; everyone else only sees the
    registrations they submitted themselves (created_by == their own id).
    """
    if role_has_permission(user.role, "registration.review"):
        records = crud.list_scoped(
            db, Registration, organization_id=user.organization_id,
            status=status, options=_LOAD_OPTIONS,
        )
    else:
        records = crud.list_scoped(
            db, Registration, organization_id=user.organization_id,
            status=status, options=_LOAD_OPTIONS, created_by=user.id,
        )
    _fill_manager_emails(db, records)
    return records


@router.post("", response_model=RegistrationOut, status_code=201, summary="Submit a Registration")
def create_registration(
    payload: RegistrationCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("registration.submit")),
):
    result = registrations.create_registration(
        db, organization_id=user.organization_id, user_id=user.id,
        data=payload.model_dump(),
    )
    _fill_manager_email(db, result)
    return result


@router.get("/{registration_id}", response_model=RegistrationOut, summary="Get a Registration")
def get_registration(
    registration_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("registration.view")),
):
    obj = crud.get_scoped_or_404(
        db, Registration, organization_id=user.organization_id,
        record_id=registration_id, options=_LOAD_OPTIONS,
    )
    _fill_manager_email(db, obj)
    return obj


@router.patch("/{registration_id}/review", response_model=RegistrationOut, summary="Approve or Reject a Registration")
def review_registration(
    registration_id: uuid.UUID,
    payload: RegistrationReview,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("registration.review")),
):
    """
    Approving creates the Team (and its Players) in the applied-for division.
    Rejecting just records the outcome with a comment; nothing is created.
    """
    obj = crud.get_scoped_or_404(
        db, Registration, organization_id=user.organization_id,
        record_id=registration_id, options=_LOAD_OPTIONS,
    )
    result = registrations.review_registration(
        db, registration=obj, user_id=user.id,
        status=payload.status, review_comment=payload.review_comment,
    )
    _fill_manager_email(db, result)
    return result


@router.patch("/{registration_id}/payment", response_model=RegistrationOut, summary="Mark registration fee as Paid/Pending")
def update_payment(
    registration_id: uuid.UUID,
    payload: PaymentUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("registration.review")),
):
    """Lets a reviewer track whether the registration fee has been paid."""
    obj = crud.get_scoped_or_404(
        db, Registration, organization_id=user.organization_id,
        record_id=registration_id, options=_LOAD_OPTIONS,
    )
    result = registrations.set_payment_status(
        db, registration=obj, user_id=user.id, payment_status=payload.payment_status,
    )
    _fill_manager_email(db, result)
    return result


@router.post("/{registration_id}/email", summary="Email the registrant about their registration fee")
def email_registrant(
    registration_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("registration.review")),
):
    """
    Sends (or, in a demo without SMTP settings, simulates) an email to the
    address the registrant typed, summarizing their registration fee and
    payment status.
    """
    obj = crud.get_scoped_or_404(
        db, Registration, organization_id=user.organization_id,
        record_id=registration_id, options=_LOAD_OPTIONS,
    )
    if not obj.contact_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This registration has no contact email to send to.",
        )
    result = send_registration_email(
        team_name=obj.team_name,
        contact_email=obj.contact_email,
        registration_fee=obj.registration_fee,
        payment_status=obj.payment_status,
        registration_status=obj.status,
    )
    return {"ok": True, **result}
