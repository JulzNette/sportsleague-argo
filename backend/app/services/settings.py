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
KEY_FOUL_LIMIT = "foul_limit"

DEFAULT_FOUL_LIMIT = 5

# Optional keys that start empty; absent = not configured yet.
_OPTIONAL_KEYS = {KEY_PRICING, KEY_REWARDS}

# Default podium prizes shown on the public Rewards page so visitors always see
# Champion / 1st / 2nd pricing even before the league administrator publishes
# their own content. An admin's configured rewards entirely replace this.
DEFAULT_REWARDS = [
    {"division": "Championship", "place": "Champion", "prize": "Champion trophy + ₱50,000 cash"},
    {"division": "Championship", "place": "1st", "prize": "Runner-up medals + ₱20,000 cash"},
    {"division": "Championship", "place": "2nd", "prize": "Bronze medals + ₱10,000 cash"},
]


def get_rewards(db: Session, *, organization_id: uuid.UUID) -> list:
    """Public Rewards page content. Always includes the Champion / 1st / 2nd
    podium: admin-configured entries are kept, and any trophy place the admin
    hasn't defined falls back to a sensible default prize - so visitors always
    see the champion, 1st, and 2nd pricing."""
    value = get_setting(db, organization_id=organization_id, key=KEY_REWARDS) or []

    existing_places = {(item.get("place") or "").strip().lower() for item in value}
    merged = list(value)
    for item in DEFAULT_REWARDS:
        if (item.get("place") or "").strip().lower() not in existing_places:
            merged.append(dict(item))
    return merged


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


def get_foul_limit(db: Session, *, organization_id: uuid.UUID) -> int:
    """Foul limit before a player is 'fouled out'. Sport-agnostic default 5."""
    value = get_setting(db, organization_id=organization_id, key=KEY_FOUL_LIMIT)
    if not value or isinstance(value, dict) and value.get("limit") is None:
        return DEFAULT_FOUL_LIMIT
    return int(value.get("limit", DEFAULT_FOUL_LIMIT))


def set_foul_limit(db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID, limit: int) -> int:
    _upsert(db, organization_id=organization_id, user_id=user_id, key=KEY_FOUL_LIMIT, value={"limit": int(limit)})
    return int(limit)


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
