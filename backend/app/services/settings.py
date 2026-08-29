"""
Read/write helpers for org-scoped app settings and division-fee overrides.

The default registration fee, the public Pricing page content, and the public
Rewards page content are each stored as a single JSON row in AppSetting. A
division can override the default fee via a DivisionFee row.
"""
import uuid
from decimal import Decimal

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.setting import AppSetting, DivisionFee

KEY_FEE = "registration_fee"
KEY_PRICING = "pricing_content"
KEY_REWARDS = "rewards_content"

# Optional keys that start empty; absent = not configured yet.
_OPTIONAL_KEYS = {KEY_PRICING, KEY_REWARDS}


def _scalar(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def get_setting(db: Session, *, organization_id: uuid.UUID, key: str) -> dict | None:
    row = (
        db.query(AppSetting)
        .filter(AppSetting.organization_id == organization_id, AppSetting.key == key)
        .first()
    )
    return row.value if row else None


def get_default_fee(db: Session, *, organization_id: uuid.UUID) -> float | None:
    value = get_setting(db, organization_id=organization_id, key=KEY_FEE)
    if not value:
        return None
    return _scalar(value.get("amount"))


def get_division_fee(
    db: Session, *, organization_id: uuid.UUID, division_id: uuid.UUID
) -> float | None:
    row = (
        db.query(DivisionFee)
        .filter(
            DivisionFee.organization_id == organization_id,
            DivisionFee.division_id == division_id,
        )
        .first()
    )
    return _scalar(row.registration_fee) if row else None


def resolve_fee(
    db: Session, *, organization_id: uuid.UUID, division_id: uuid.UUID
) -> float:
    """Source of truth for a registration's fee: division override, else global
    default, else raise a clear 400 so a submission can't slip through unpriced.
    """
    override = get_division_fee(db, organization_id=organization_id, division_id=division_id)
    if override is not None:
        return override
    default_fee = get_default_fee(db, organization_id=organization_id)
    if default_fee is not None:
        return default_fee
    raise HTTPException(
        status_code=http_status.HTTP_400_BAD_REQUEST,
        detail=(
            "No registration fee is configured. An administrator must set either a "
            "default fee or a fee for this division before registration."
        ),
    )


def set_default_fee(db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID, amount: float | None) -> float | None:
    _upsert(
        db, organization_id=organization_id, user_id=user_id, key=KEY_FEE,
        value={"amount": float(amount)},
    )
    return _scalar(amount)


def set_content(
    db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID, key: str, value: list
) -> list:
    if key not in _OPTIONAL_KEYS:
        raise HTTPException(status_code=422, detail=f"Unknown settings key '{key}'.")
    _upsert(db, organization_id=organization_id, user_id=user_id, key=key, value=value)
    return value


def set_division_fee(
    db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID,
    division_id: uuid.UUID, amount: float,
) -> DivisionFee:
    row = (
        db.query(DivisionFee)
        .filter(DivisionFee.organization_id == organization_id, DivisionFee.division_id == division_id)
        .first()
    )
    if row is None:
        row = DivisionFee(
            organization_id=organization_id,
            created_by=user_id,
            updated_by=user_id,
            division_id=division_id,
            registration_fee=amount,
        )
        db.add(row)
    else:
        row.registration_fee = amount
        row.updated_by = user_id
    db.commit()
    db.refresh(row)
    return row


def clear_division_fee(
    db: Session, *, organization_id: uuid.UUID, division_id: uuid.UUID
) -> None:
    row = (
        db.query(DivisionFee)
        .filter(DivisionFee.organization_id == organization_id, DivisionFee.division_id == division_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No fee override for this division.")
    db.delete(row)
    db.commit()


def list_division_fees(db: Session, *, organization_id: uuid.UUID) -> list[DivisionFee]:
    return (
        db.query(DivisionFee)
        .filter(DivisionFee.organization_id == organization_id)
        .order_by(DivisionFee.created_at)
        .all()
    )


def _upsert(db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID, key: str, value) -> None:
    row = (
        db.query(AppSetting)
        .filter(AppSetting.organization_id == organization_id, AppSetting.key == key)
        .first()
    )
    if row is None:
        row = AppSetting(
            organization_id=organization_id, created_by=user_id, updated_by=user_id,
            key=key, value=value,
        )
        db.add(row)
    else:
        row.value = value
        row.updated_by = user_id
    db.commit()
