"""
Per-match player statistics: view the current lines, or replace them all at
once when a result is recorded. Stats are only accepted once a match is
Completed/Forfeited, and only for players on the two teams that actually
played.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db_session, require_permission
from app.models.match import Match
from app.models.player import Player
from app.models.player_stat import PlayerGameStat
from app.models.team import Team
from app.schemas.player_stat import LiveStatOut, LiveStatUpdateIn, PlayerStatOut, PlayerStatsSubmit
from app.services import crud, settings as settings_service

router = APIRouter(prefix="/matches/{match_id}/stats", tags=["Player Stats"])


def _match_stats_rows(db: Session, *, organization_id: uuid.UUID, match_id: uuid.UUID):
    query = (
        select(PlayerGameStat, Player.full_name, Team.name)
        .join(Player, Player.id == PlayerGameStat.player_id)
        .join(Team, Team.id == PlayerGameStat.team_id)
        .where(
            PlayerGameStat.organization_id == organization_id,
            PlayerGameStat.match_id == match_id,
            PlayerGameStat.deleted_at.is_(None),
        )
    )
    return db.execute(query).all()


@router.get("", response_model=list[PlayerStatOut], summary="Get Match Player Stats")
def get_match_stats(
    match_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player_stat.view")),
):
    crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    return [
        PlayerStatOut(
            match_id=row.PlayerGameStat.match_id,
            player_id=row.PlayerGameStat.player_id,
            team_id=row.PlayerGameStat.team_id,
            player_name=row[1],
            team_name=row[2],
            points=row.PlayerGameStat.points,
            assists=row.PlayerGameStat.assists,
            fouls=row.PlayerGameStat.fouls,
            rebounds=row.PlayerGameStat.rebounds,
            steals=row.PlayerGameStat.steals,
        )
        for row in _match_stats_rows(db, organization_id=user.organization_id, match_id=match_id)
    ]


@router.post("", response_model=list[PlayerStatOut], status_code=201, summary="Replace Match Player Stats")
def submit_match_stats(
    match_id: uuid.UUID,
    payload: PlayerStatsSubmit,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("player_stat.enter")),
):
    match = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    if match.status not in {"Completed", "Forfeited"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player stats can only be entered for a completed or forfeited match.",
        )

    # Resolve which players belong to the two teams that played, and which
    # team each player is on - a player must be on one of the match's teams.
    team_ids = {match.home_team_id, match.away_team_id}
    team_names = {t.id: t.name for t in db.execute(select(Team).where(Team.id.in_(team_ids))).scalars()}
    player_meta: dict[uuid.UUID, tuple[str, uuid.UUID]] = {}
    players = db.execute(
        select(Player).where(
            Player.organization_id == user.organization_id,
            Player.team_id.in_(team_ids),
            Player.deleted_at.is_(None),
        )
    ).scalars()
    for player in players:
        player_meta[player.id] = (player.full_name, player.team_id)

    lines = []
    for line in payload.lines:
        meta = player_meta.get(line.player_id)
        if meta is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Player {line.player_id} is not on either team in this match.",
            )
        lines.append((line, meta))

    # Replace the match's whole stats set: hard-delete old rows, insert new.
    db.query(PlayerGameStat).filter(
        PlayerGameStat.organization_id == user.organization_id,
        PlayerGameStat.match_id == match_id,
    ).delete(synchronize_session=False)
    db.flush()

    for line, (_, team_id) in lines:
        db.add(PlayerGameStat(
            organization_id=user.organization_id,
            match_id=match_id,
            player_id=line.player_id,
            team_id=team_id,
            points=line.points,
            assists=line.assists,
            fouls=line.fouls,
            rebounds=line.rebounds,
            steals=line.steals,
            created_by=user.id,
            updated_by=user.id,
        ))
    db.commit()

    return [
        PlayerStatOut(
            match_id=match_id,
            player_id=line.player_id,
            team_id=team_id,
            player_name=name,
            team_name=team_names.get(team_id, ""),
            points=line.points,
            assists=line.assists,
            fouls=line.fouls,
            rebounds=line.rebounds,
            steals=line.steals,
        )
        for line, (name, team_id) in lines
    ]


@router.post("/live", response_model=LiveStatOut, status_code=200, summary="Live per-player stat update")
def submit_live_stat(
    match_id: uuid.UUID,
    payload: LiveStatUpdateIn,
    db: Session = Depends(get_db_session),
    user: CurrentUser = Depends(require_permission("result.update")),
):
    """Add points and/or fouls to a single player for a match that is underway,
    building the live scoring grid. Player stats rows are upserted on first
    touch so the grid can grow during the game. The foul limit (default 5)
    comes from the org setting; a player at or above it is marked 'fouled out'.
    """
    match = crud.get_scoped_or_404(db, Match, organization_id=user.organization_id, record_id=match_id)
    if match.status in {"Completed", "Forfeited", "Cancelled"}:
        raise HTTPException(status_code=400, detail="Live scoring is unavailable for a finished match.")

    player = db.execute(
        select(Player).where(
            Player.organization_id == user.organization_id,
            Player.id == payload.player_id,
            Player.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    team_ids = {match.home_team_id, match.away_team_id}
    if player.team_id not in team_ids:
        raise HTTPException(status_code=400, detail="Player is not on either team in this match.")

    stat = (
        db.query(PlayerGameStat)
        .filter(
            PlayerGameStat.organization_id == user.organization_id,
            PlayerGameStat.match_id == match_id,
            PlayerGameStat.player_id == payload.player_id,
        )
        .first()
    )
    if stat is None:
        stat = PlayerGameStat(
            organization_id=user.organization_id,
            match_id=match_id,
            player_id=player.id,
            team_id=player.team_id,
            points=0, assists=0, fouls=0, rebounds=0, steals=0,
            created_by=user.id, updated_by=user.id,
        )
        db.add(stat)
    stat.points += payload.points
    stat.fouls += payload.fouls
    stat.updated_by = user.id
    db.commit()
    db.refresh(stat)

    foul_limit = settings_service.get_foul_limit(db, organization_id=user.organization_id)
    team_name = db.execute(select(Team.name).where(Team.id == stat.team_id)).scalar_one_or_none() or ""
    return LiveStatOut(
        match_id=stat.match_id,
        player_id=stat.player_id,
        team_id=stat.team_id,
        player_name=player.full_name,
        team_name=team_name,
        points=stat.points,
        assists=stat.assists,
        fouls=stat.fouls,
        rebounds=stat.rebounds,
        steals=stat.steals,
        fouls_out=stat.fouls >= foul_limit,
        foul_limit=foul_limit,
    )
