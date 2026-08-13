"""
Test setup: the whole suite runs against an in-memory SQLite database, never
the real Neon database.

- `import app.models` registers every table on Base.metadata.
- app.dependency_overrides[get_db] points FastAPI's DB dependency at the test
  session factory, so no request ever touches the configured DATABASE_URL.
- Rate-limit counters are reset before/after every test so auth tests can hit
  login/register/change-password repeatedly without tripping 429s.
"""
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register every table on Base.metadata
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.stub import Organization
from app.models.league import League
from app.models.season import Season
from app.models.division import Division
from app.models.team import Team
from app.models.match import Match
from app.models.match_result import MatchResult

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.fixture()
def dbsession():
    """A direct SQLAlchemy session for seeding test data."""
    Base.metadata.create_all(test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(test_engine)


@pytest.fixture()
def client(org):
    """FastAPI TestClient whose /api/v1 routes resolve against the test DB.

    Depends on the `org` fixture so that exactly one organization exists and
    register/login/standings all resolve against the same org as seeded data.
    """
    Base.metadata.create_all(test_engine)

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)


@pytest.fixture()
def org(dbsession):
    org = Organization(name="Test Org")
    dbsession.add(org)
    dbsession.commit()
    dbsession.refresh(org)
    return org


@pytest.fixture()
def season_division_teams(dbsession, org):
    """One season with one division and four teams: Team A/B/C/D.

    Each parent is flushed before its id is referenced by a child so the
    NOT NULL FK columns always receive a real value.
    """
    league = League(organization_id=org.id, name="Test League", sport_type="Basketball", status="Active",
                    created_by=org.id, updated_by=org.id)
    dbsession.add(league)
    dbsession.flush()

    season = Season(organization_id=org.id, league_id=league.id, name="Season 1",
                    start_date=date(2026, 1, 1), end_date=date(2026, 6, 30),
                    format="Round Robin", status="Active",
                    created_by=org.id, updated_by=org.id)
    dbsession.add(season)
    dbsession.flush()

    division = Division(organization_id=org.id, season_id=season.id, name="Open", max_teams=8,
                        status="Active", created_by=org.id, updated_by=org.id)
    dbsession.add(division)
    dbsession.flush()

    teams = [
        Team(organization_id=org.id, division_id=division.id, name=f"Team {name}", status="Active",
             created_by=org.id, updated_by=org.id)
        for name in ("A", "B", "C", "D")
    ]
    dbsession.add_all(teams)
    dbsession.commit()
    for obj in [league, season, division, *teams]:
        dbsession.refresh(obj)
    return season, division, {t.name.replace("Team ", ""): t for t in teams}


@pytest.fixture()
def add_match(dbsession):
    """Creates a completed (or otherwise) match + result and returns the Match."""
    def _add(season, division, home, away, *, org_id,
             home_score=0, away_score=0, result_type="Normal",
             forfeit_winner_team_id=None, status="Completed"):
        match = Match(
            organization_id=org_id, season_id=season.id, division_id=division.id,
            home_team_id=home.id, away_team_id=away.id,
            scheduled_date=date(2026, 2, 1), scheduled_time=time(18, 0), venue="Court 1",
            round_number=1, match_type="Regular", status=status,
            created_by=org_id, updated_by=org_id,
        )
        result = MatchResult(
            organization_id=org_id,
            home_score=home_score, away_score=away_score,
            result_type=result_type, forfeit_winner_team_id=forfeit_winner_team_id,
            submitted_by=org_id, created_by=org_id, updated_by=org_id,
        )
        match.result = result
        dbsession.add(match)
        dbsession.commit()
        return match
    return _add
