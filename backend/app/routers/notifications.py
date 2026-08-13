import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.notification import Notification
from app.schemas.notification import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut], summary="List My Notifications")
def list_notifications(
    limit: int = 50,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("notification.view")),
):
    """Only ever returns notifications addressed to the current user."""
    stmt = (
        select(Notification)
        .where(Notification.organization_id == user.organization_id, Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


@router.get("/unread-count", response_model=UnreadCountOut, summary="Unread Notification Count")
def unread_count(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("notification.view")),
):
    count = db.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.organization_id == user.organization_id,
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
    ).scalar_one()
    return {"count": count}


@router.patch("/{notification_id}/read", response_model=NotificationOut, summary="Mark Notification Read")
def mark_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("notification.view")),
):
    obj = db.execute(
        select(Notification).where(
            Notification.organization_id == user.organization_id,
            Notification.user_id == user.id,
            Notification.id == notification_id,
        )
    ).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    obj.is_read = True
    obj.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/read-all", response_model=UnreadCountOut, summary="Mark All Notifications Read")
def mark_all_read(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("notification.view")),
):
    rows = db.execute(
        select(Notification).where(
            Notification.organization_id == user.organization_id,
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
    ).scalars().all()
    now = datetime.now(timezone.utc)
    for row in rows:
        row.is_read = True
        row.read_at = now
    db.commit()
    return {"count": 0}
