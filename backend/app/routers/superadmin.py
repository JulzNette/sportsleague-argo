"""
Superadmin portal summary (System Administrator / Superadmin only).

This is the read-only command center backing the /superadmin page: one request
returns every org-wide count plus the registration pipeline and the user role
distribution, so the portal renders a single authoritative overview instead of
orchestrating many list calls client-side.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.coach import Coach
from app.models.division import Division
from app.models.league import League
from app.models.match import Match
from app.models.player import Player
from app.models.referee import Referee
from app.models.registration import Registration
from app.models.season import Season
from app.models.stub import User
from app.models.team import Team

router = APIRouter(prefix="/superadmin", tags=["Superadmin"])

# (label -> model). Every model here is scoped by organization_id and, where it
# supports soft-delete, only counts the still-active rows.
_TABLES = [
    ("leagues", League),
    ("seasons", Season),
    ("divisions", Division),
    ("teams", Team),
    ("players", Player),
    ("coaches", Coach),
    ("referees", Referee),
    ("matches", Match),
]


def _count(db: Session, model, org_id):
    stmt = select(func.count()).where(model.organization_id == org_id)
    if hasattr(model, "deleted_at"):
        stmt = stmt.where(model.deleted_at.is_(None))
    return db.execute(stmt).scalar_one()


@router.get("/summary", summary="Org-wide summary for the superadmin portal")
def superadmin_summary(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("settings.manage")),
):
    counts = {name: _count(db, model, user.organization_id) for name, model in _TABLES}
    counts["users"] = db.execute(
        select(func.count()).where(User.organization_id == user.organization_id)
    ).scalar_one()

    registrations = {}
    for status in ("Pending", "Approved", "Rejected"):
        registrations[status.lower()] = db.execute(
            select(func.count()).where(
                Registration.organization_id == user.organization_id,
                Registration.status == status,
            )
        ).scalar_one()

    role_rows = db.execute(
        select(User.role, func.count())
        .where(User.organization_id == user.organization_id)
        .group_by(User.role)
        .order_by(User.role)
    ).all()
    users_by_rule = {role: count for role, count in role_rows}

    return {
        "counts": counts,
        "registrations": registrations,
        "users_by_role": users_by_rule,
    }
