"""
Notification dispatch for the registration workflow. Every helper only
builds rows on the given session - the caller's transaction commits them
alongside the action that triggered them, so a notification can never be
sent for an action that never happened.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import PERMISSIONS
from app.models.notification import Notification
from app.models.registration import Registration
from app.models.stub import User


def _notify(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor_id: uuid.UUID,
    user_id: uuid.UUID,
    type: str,
    title: str,
    message: str | None,
    registration_id: uuid.UUID | None,
):
    db.add(
        Notification(
            organization_id=organization_id,
            created_by=actor_id,
            updated_by=actor_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            registration_id=registration_id,
            is_read=False,
        )
    )


def notify_reviewers(db: Session, *, organization_id: uuid.UUID, actor_id: uuid.UUID, registration: Registration):
    """Notify every active user whose role can review registrations."""
    roles = PERMISSIONS["registration.review"]
    reviewer_ids = db.execute(
        select(User.id).where(
            User.organization_id == organization_id,
            User.role.in_(roles),
            User.is_active.is_(True),
        )
    ).scalars().all()
    for reviewer_id in reviewer_ids:
        _notify(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            user_id=reviewer_id,
            type="registration.submitted",
            title=f"New registration: {registration.team_name}",
            message=f"{registration.team_name} applied to join a division and is awaiting your review.",
            registration_id=registration.id,
        )


def notify_submitter(db: Session, *, organization_id: uuid.UUID, actor_id: uuid.UUID, registration: Registration):
    """Notify whoever submitted the registration about its outcome."""
    _notify(
        db,
        organization_id=organization_id,
        actor_id=actor_id,
        user_id=registration.created_by,
        type=f"registration.{registration.status.lower()}",
        title=f"Registration {registration.status.lower()}: {registration.team_name}",
        message=(
            f"Your registration for {registration.team_name} was {registration.status.lower()}"
            + (" and a team was created." if registration.status == "Approved" else ".")
        ),
        registration_id=registration.id,
    )
