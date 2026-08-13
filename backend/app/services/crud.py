"""
Small generic CRUD helpers shared by the simple per-entity routers, so that
tenant scoping (organization_id) and audit stamping (created_by/updated_by)
are applied in exactly one place instead of being re-typed in every router.
"""
import uuid
from datetime import datetime, timezone
from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


def _active_filter(model, stmt):
    """Exclude soft-deleted rows (archived rows only show up in archive lists)."""
    return stmt.where(model.deleted_at.is_(None))


def list_scoped(db: Session, model, *, organization_id: uuid.UUID, options: list | None = None, **filters):
    stmt = select(model).where(model.organization_id == organization_id)
    for field, value in filters.items():
        if value is not None:
            stmt = stmt.where(getattr(model, field) == value)
    stmt = _active_filter(model, stmt)
    if options:
        stmt = stmt.options(*options)
    return db.execute(stmt.order_by(model.created_at.desc())).scalars().all()


def list_archived_scoped(db: Session, model, *, organization_id: uuid.UUID, **filters):
    stmt = select(model).where(model.organization_id == organization_id, model.deleted_at.is_not(None))
    for field, value in filters.items():
        if value is not None:
            stmt = stmt.where(getattr(model, field) == value)
    return db.execute(stmt.order_by(model.deleted_at.desc())).scalars().all()


def get_scoped_or_404(db: Session, model, *, organization_id: uuid.UUID, record_id: uuid.UUID, include_archived: bool = False):
    stmt = select(model).where(model.organization_id == organization_id, model.id == record_id)
    if not include_archived:
        stmt = _active_filter(model, stmt)
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj


def create_scoped(db: Session, model, *, organization_id: uuid.UUID, user_id: uuid.UUID, data: dict):
    obj = model(organization_id=organization_id, created_by=user_id, updated_by=user_id, **data)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This record conflicts with an existing one (duplicate or invalid reference).",
        ) from exc
    db.refresh(obj)
    return obj


def update_scoped(db: Session, obj, *, user_id: uuid.UUID, data: dict):
    for field, value in data.items():
        setattr(obj, field, value)
    obj.updated_by = user_id
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This update conflicts with an existing record.",
        ) from exc
    db.refresh(obj)
    return obj


def delete_scoped(db: Session, obj):
    """Soft-delete: mark the row as archived instead of removing it."""
    obj.deleted_at = datetime.now(timezone.utc)
    db.commit()


def restore_scoped(db: Session, obj):
    """Bring an archived row back to the active set."""
    obj.deleted_at = None
    db.commit()
    db.refresh(obj)
    return obj


def purge_scoped(db: Session, obj):
    """Hard-delete: permanently remove an archived row."""
    db.delete(obj)
    db.commit()
