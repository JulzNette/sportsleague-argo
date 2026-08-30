import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, aliased

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.core.state_machines import MATCH_STATUS_TRANSITIONS, is_valid_transition
from app.models.match import Match
from app.models.team import Team
from app.models.division import Division
from app.models.season import Season
from app.models.league import League
from app.models.stub import Organization
from app.models.match_result import MatchResult
from app.schemas.match import MatchCreate, MatchOut, MatchStatusUpdate, MatchUpdate, PublicMatchOut
from app.services import crud

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/public", response_model=list[PublicMatchOut], summary="Public Match Schedule")
def public_schedule(db: Session = Depends(get_db_session)):
    """Public read-only schedule for the landing page. No auth required.

    Shows only upcoming/in-progress matches (completed ones are dropped) and
    only basketball — the sport the public landing page showcases.
    """
    org = db.execute(select(Organization).limit(1)).scalar_one_or_none()
    if org is None:
        return []
    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)
    rows = (
        db.execute(
            select(Match, HomeTeam.name.label("home_name"), AwayTeam.name.label("away_name"),
                   Division.name.label("division_name"), Season.name.label("season_name"), MatchResult)
            .join(HomeTeam, HomeTeam.id == Match.home_team_id)
            .join(AwayTeam, AwayTeam.id == Match.away_team_id)
            .join(Division, Division.id == Match.division_id)
            .join(Season, Season.id == Match.season_id)
            .join(League, League.id == Season.league_id)
            .outerjoin(MatchResult, MatchResult.match_id == Match.id)
            .where(
                Match.organization_id == org.id,
                Match.deleted_at.is_(None),
                Match.status.in_(["Scheduled", "In Progress", "Postponed"]),
                League.sport_type.ilike("%basketball%"),
            )
            .order_by(Match.scheduled_date, Match.scheduled_time)
        )
        .all()
    )
    now = datetime.now()
    out = []
    for (m, home_name, away_name, division_name, season_name, r) in rows:
        live = m.status == "In Progress" and now >= datetime.combine(m.scheduled_date, m.scheduled_time)
        display_status = "In Progress" if live else ("Scheduled" if m.status == "In Progress" else m.status)
        out.append(
            PublicMatchOut(
                id=m.id,
                home_team=home_name,
                away_team=away_name,
                division=division_name,
                season=season_name,
                scheduled_date=m.scheduled_date,
                scheduled_time=m.scheduled_time,
                venue=m.venue,
                round_number=m.round_number,
                match_type=m.match_type,
                status=display_status,
                home_score=(r.home_score if r else None) if live else None,
                away_score=(r.away_score if r else None) if live else None,
                period=(r.period if r else None) if live else None,
                minutes=(r.minutes if r else None) if live else None,
                seconds=(r.seconds if r else None) if live else None,
            )
        )
    return out


@router.get("", response_model=list[MatchOut], summary="List Matches")
def list_matches(
    season_id: uuid.UUID | None = None,
    division_id: uuid.UUID | None = None,
    status_: str | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.view")),
):
    return crud.list_scoped(
        db, Match, organization_id=user.organization_id,
        season_id=season_id, division_id=division_id, status=status_,
        options=[selectinload(Match.result)],
    )


@router.get("/archived", response_model=list[MatchOut], summary="List Archived Matches")
def list_archived_matches(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.view")),
):
    return crud.list_archived_scoped(db, Match, organization_id=user.organization_id)


@router.get("/{match_id}", response_model=MatchOut, summary="Get Match")
def get_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.view")),
):
    return crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)


@router.post("", response_model=MatchOut, status_code=201, summary="Create Match")
def schedule_match(
    payload: MatchCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.schedule")),
):
    return crud.create_scoped(
        db, Match, organization_id=user.organization_id, user_id=user.id, data=payload.model_dump()
    )


@router.patch("/{match_id}", response_model=MatchOut, summary="Update Match")
def update_match(
    match_id: uuid.UUID,
    payload: MatchUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    return crud.update_scoped(db, obj, user_id=user.id, data=payload.model_dump(exclude_unset=True))


@router.post("/{match_id}/assign-referee", response_model=MatchOut, summary="Assign Referee")
def assign_referee(
    match_id: uuid.UUID,
    referee_id: uuid.UUID | None = None,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("assignment.create")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    return crud.update_scoped(db, obj, user_id=user.id, data={"referee_id": referee_id})


@router.post("/{match_id}/status", response_model=MatchOut, summary="Update Match Status")
def transition_match_status(
    match_id: uuid.UUID,
    payload: MatchStatusUpdate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    if not is_valid_transition(MATCH_STATUS_TRANSITIONS, obj.status, payload.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition match from '{obj.status}' to '{payload.status}'",
        )
    return crud.update_scoped(db, obj, user_id=user.id, data={"status": payload.status})


@router.delete("/{match_id}", status_code=204, summary="Delete Match")
def delete_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    crud.delete_scoped(db, obj)


@router.post("/{match_id}/restore", response_model=MatchOut, summary="Restore Match")
def restore_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(
        db, Match, organization_id=user.organization_id, record_id=match_id, include_archived=True
    )
    return crud.restore_scoped(db, obj)


@router.delete("/{match_id}/purge", status_code=204, summary="Permanently Delete Match")
def purge_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("match.update")),
):
    obj = crud.get_scoped_or_404(
        db, Match, organization_id=user.organization_id, record_id=match_id, include_archived=True
    )
    crud.purge_scoped(db, obj)
