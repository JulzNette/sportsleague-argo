"""
Reports store only metadata; viewing a report recomputes its content
(standings) live from current data - nothing derived is persisted.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.division import Division
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportOut
from app.schemas.standing import StandingRow
from app.services import crud
from app.services.standings import compute_standings

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=list[ReportOut], summary="List Reports")
def list_reports(
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("report.view")),
):
    return crud.list_scoped(db, Report, organization_id=user.organization_id)


@router.post("", response_model=ReportOut, status_code=201, summary="Generate Report")
def generate_report(
    payload: ReportCreate,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("report.generate")),
):
    data = payload.model_dump()
    data["generated_by"] = user.id
    return crud.create_scoped(db, Report, organization_id=user.organization_id, user_id=user.id, data=data)


@router.get("/{report_id}/standings", response_model=list[StandingRow], summary="Get Report Standings")
def view_report_standings(
    report_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("report.view")),
):
    """
    Returns the live standings table for a report scoped to a season
    (optionally narrowed to a division), recomputed fresh every call.
    """
    report = crud.get_scoped_or_404(db, Report, organization_id=user.organization_id, record_id=report_id)
    if report.division_id is not None:
        return compute_standings(
            db, organization_id=user.organization_id,
            season_id=report.season_id, division_id=report.division_id,
        )
    all_rows: list[dict] = []
    if report.season_id is not None:
        divisions = crud.list_scoped(db, Division, organization_id=user.organization_id, season_id=report.season_id)
        for division in divisions:
            all_rows.extend(
                compute_standings(
                    db, organization_id=user.organization_id,
                    season_id=report.season_id, division_id=division.id,
                )
            )
    return all_rows
