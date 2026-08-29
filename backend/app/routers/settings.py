import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.schemas.setting import (
    AdminSettingsOut, ContentUpdate, DivisionFeeIn, DivisionFeeOut,
    FeeConfigUpdate, PublicSettingsOut,
)
from app.services import settings as settings_service

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/public", response_model=PublicSettingsOut, summary="Public Pricing & Rewards")
def public_settings(
    db: Session = Depends(get_db_session),
):
    """Unauthenticated: exposes the default registration fee plus the Pricing
    and Rewards page content for the first organization in the database (the
    same convention used by the public match schedule).
    """
    org = _first_org(db)
    if org is None:
        return PublicSettingsOut()
    return PublicSettingsOut(
        registration_fee=settings_service.get_default_fee(db, organization_id=org.id),
        pricing=settings_service.get_setting(db, organization_id=org.id, key=settings_service.KEY_PRICING) or [],
        rewards=settings_service.get_setting(db, organization_id=org.id, key=settings_service.KEY_REWARDS) or [],
    )


@router.get("/public/divisions/{division_id}/fee", summary="Public fee for a division")
def public_division_fee(
    division_id: uuid.UUID,
    db: Session = Depends(get_db_session),
):
    """Resolve the registration fee a team would pay for a given division
    (per-division override, else the default). Unauthenticated so registrants
    can see the exact amount on the registration form.
    """
    from app.models.division import Division
    division = db.get(Division, division_id)
    if division is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Division not found")
    fee = settings_service.resolve_fee(
        db, organization_id=division.organization_id, division_id=division.id,
    )
    return {"division_id": division_id, "registration_fee": fee}


@router.get("", response_model=AdminSettingsOut, summary="Admin Settings (fee, pricing, rewards)")
def admin_settings(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("settings.manage")),
):
    org_id = user.organization_id
    default_fee = settings_service.get_default_fee(db, organization_id=org_id)
    fees = settings_service.list_division_fees(db, organization_id=org_id)
    return AdminSettingsOut(
        registration_fee=default_fee,
        configured_fee=default_fee is not None,
        pricing=settings_service.get_setting(db, organization_id=org_id, key=settings_service.KEY_PRICING) or [],
        rewards=settings_service.get_setting(db, organization_id=org_id, key=settings_service.KEY_REWARDS) or [],
        division_fees=[DivisionFeeOut.model_validate(f, from_attributes=True) for f in fees],
    )


@router.put("/fee", response_model=FeeConfigUpdate, summary="Set the default registration fee")
def set_fee(
    payload: FeeConfigUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("settings.manage")),
):
    settings_service.set_default_fee(
        db, organization_id=user.organization_id, user_id=user.id, amount=payload.amount,
    )
    return payload


@router.put("/content", response_model=ContentUpdate, summary="Set Pricing or Rewards page content")
def set_content(
    payload: ContentUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("settings.manage")),
):
    settings_service.set_content(
        db, organization_id=user.organization_id, user_id=user.id,
        key=payload.key, value=payload.items,
    )
    return payload


@router.put("/division-fees", response_model=DivisionFeeOut, summary="Set a per-division registration fee")
def set_division_fee(
    payload: DivisionFeeIn,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("settings.manage")),
):
    row = settings_service.set_division_fee(
        db, organization_id=user.organization_id, user_id=user.id,
        division_id=payload.division_id, amount=payload.registration_fee,
    )
    return DivisionFeeOut.model_validate(row, from_attributes=True)


@router.delete("/division-fees/{division_id}", status_code=204, summary="Clear a per-division fee override")
def clear_division_fee(
    division_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("settings.manage")),
):
    settings_service.clear_division_fee(
        db, organization_id=user.organization_id, division_id=division_id,
    )


def _first_org(db: Session):
    from app.models.stub import Organization
    return db.query(Organization).order_by(Organization.created_at).first()
