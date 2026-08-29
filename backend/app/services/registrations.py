"""
Registration workflow logic that CRUD helpers can't express: submitting a
registration with its nested roster/documents, and reviewing it. Reviewing
is where the feature earns its keep - approving materializes the registration
into a real Team (+ Players) in the division it applied for.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.coach import Coach
from app.models.player import Player
from app.models.registration import Registration, RegistrationDocument, RegistrationPlayer
from app.models.stub import User
from app.models.team import Team
from app.services import settings as settings_service
from app.services.email import send_registration_ack_email
from app.services.notifications import notify_reviewers, notify_submitter


def create_registration(db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID, data: dict):
    # The registration fee is always the admin-configured amount (source of
    # truth): a per-division override if set, otherwise the org-wide default.
    # The division row must exist for the lookup to work, so resolve it first.
    from app.models.division import Division
    division = db.get(Division, data["division_id"])
    if division is None or division.organization_id != organization_id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="The selected division is invalid.",
        )
    fee = settings_service.resolve_fee(db, organization_id=organization_id, division_id=data["division_id"])

    registration = Registration(
        organization_id=organization_id,
        created_by=user_id,
        updated_by=user_id,
        division_id=data["division_id"],
        team_name=data["team_name"],
        coach_name=data.get("coach_name"),
        contact_email=data.get("contact_email"),
        contact_phone=data.get("contact_phone"),
        notes=data.get("notes"),
        status="Pending",
        registration_fee=fee,
        payment_status="Pending",
    )
    registration.players = [
        RegistrationPlayer(
            organization_id=organization_id, created_by=user_id, updated_by=user_id, **p
        )
        for p in data["players"]
    ]
    registration.documents = [
        RegistrationDocument(
            organization_id=organization_id, created_by=user_id, updated_by=user_id, **d
        )
        for d in (data.get("documents") or [])
    ]
    db.add(registration)
    db.flush()
    notify_reviewers(db, organization_id=organization_id, actor_id=user_id, registration=registration)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="This team already has a registration (pending or not) in this division.",
        ) from exc
    db.refresh(registration)

    # Auto-email the manager (the account that submitted) an acknowledgment.
    # Wrapped in try/except so an email hiccup never fails the registration.
    try:
        submitter = db.get(User, user_id)
        manager_email = submitter.email if submitter else None
        if manager_email:
            send_registration_ack_email(team_name=registration.team_name, manager_email=manager_email)
    except Exception:  # noqa: BLE001 - email is best-effort and must not block
        pass

    return registration


def review_registration(
    db: Session,
    *,
    registration: Registration,
    user_id: uuid.UUID,
    status: str,
    review_comment: str | None,
):
    if registration.status != "Pending":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review a registration that is '{registration.status}'.",
        )

    if status == "Approved":
        team = Team(
            organization_id=registration.organization_id,
            created_by=user_id,
            updated_by=user_id,
            division_id=registration.division_id,
            name=registration.team_name,
            coach_name=registration.coach_name,
            contact_email=registration.contact_email,
            contact_phone=registration.contact_phone,
            status="Active",
        )
        team.players = [
            Player(
                organization_id=registration.organization_id,
                created_by=user_id,
                updated_by=user_id,
                full_name=p.full_name,
                date_of_birth=p.date_of_birth,
                position=p.position,
                jersey_number=p.jersey_number,
                contact_phone=p.contact_phone,
                status="Active",
            )
            for p in registration.players
        ]
        db.add(team)
        # Materialize the team so its id exists, then auto-create the coach
        # record from the registration's coach info (name/email/phone) - the
        # Team Manager picks the coach when they fill in the registration form.
        db.flush()
        if registration.coach_name:
            db.add(Coach(
                organization_id=registration.organization_id,
                created_by=user_id,
                updated_by=user_id,
                team_id=team.id,
                full_name=registration.coach_name,
                role="Head Coach",
                email=registration.contact_email,
                phone=registration.contact_phone,
                status="Active",
            ))

    registration.status = status
    registration.reviewed_by = user_id
    registration.reviewed_at = datetime.now(timezone.utc)
    registration.review_comment = review_comment

    notify_submitter(db, organization_id=registration.organization_id, actor_id=user_id, registration=registration)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=(
                "Could not complete the review - the team name is already taken "
                "by an existing team in this division."
            ),
        ) from exc
    db.refresh(registration)
    return registration


def set_payment_status(
    db: Session,
    *,
    registration: Registration,
    user_id: uuid.UUID,
    payment_status: str,
):
    if payment_status not in ("Pending", "Paid"):
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payment status '{payment_status}'.",
        )
    registration.payment_status = payment_status
    registration.updated_by = user_id
    db.commit()
    db.refresh(registration)
    return registration
