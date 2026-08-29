"""
Live scoring grid: per-player points/fouls can be added during a match and the
player is marked 'fouled out' at the configured foul limit.
"""
import pytest

from app.core.security import hash_password
from app.models.player import Player
from app.models.stub import User
from app.models.setting import AppSetting


@pytest.fixture()
def admin(dbsession, org):
    user = User(
        organization_id=org.id,
        email="admin.scoring@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin",
        role="System Administrator",
        is_active=True,
    )
    dbsession.add(user)
    dbsession.commit()
    dbsession.refresh(user)
    return user


@pytest.fixture()
def players(dbsession, org, season_division_teams):
    _, _, teams = season_division_teams
    roster = [
        Player(organization_id=org.id, team_id=teams["A"].id, full_name="Home Play",
               jersey_number="1", status="Active", created_by=org.id, updated_by=org.id),
        Player(organization_id=org.id, team_id=teams["B"].id, full_name="Away Play",
               jersey_number="2", status="Active", created_by=org.id, updated_by=org.id),
    ]
    dbsession.add_all(roster)
    dbsession.commit()
    for p in roster:
        dbsession.refresh(p)
    return roster


def _admin_headers(client, admin):
    login = client.post("/api/v1/auth/login", json={"email": admin.email, "password": "adminpass123"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_live_scoring_fouls_out(client, dbsession, org, season_division_teams, players, add_match, admin):
    season, division, teams = season_division_teams
    # Start the game (status In Progress so live scoring is allowed).
    match = add_match(season, division, teams["A"], teams["B"], org_id=org.id, status="In Progress")
    headers = _admin_headers(client, admin)
    url = f"/api/v1/matches/{match.id}/stats/live"
    home = players[0]

    first = client.post(url, json={"player_id": str(home.id), "points": 2, "fouls": 1}, headers=headers)
    assert first.status_code == 200
    assert first.json()["points"] == 2
    assert first.json()["fouls"] == 1
    assert first.json()["fouls_out"] is False
    assert first.json()["foul_limit"] == 5

    # Two more fouls -> total 3, still not out.
    client.post(url, json={"player_id": str(home.id), "fouls": 2}, headers=headers)
    # Two more -> total 5 => equals the limit => fouled out.
    out = client.post(url, json={"player_id": str(home.id), "fouls": 2}, headers=headers)
    assert out.status_code == 200
    assert out.json()["fouls"] == 5
    assert out.json()["fouls_out"] is True

    # Grid reflects the player too (GET match stats).
    grid = client.get(f"/api/v1/matches/{match.id}/stats", headers=headers)
    assert grid.status_code == 200
    assert any(r["player_name"] == "Home Play" and r["fouls"] == 5 for r in grid.json())


def test_live_scoring_rejects_finished_and_foreign(client, dbsession, org, season_division_teams, players, add_match, admin):
    season, division, teams = season_division_teams
    done = add_match(season, division, teams["A"], teams["B"], org_id=org.id, status="Completed")
    headers = _admin_headers(client, admin)

    finished = client.post(
        f"/api/v1/matches/{done.id}/stats/live",
        json={"player_id": str(players[0].id), "fouls": 1}, headers=headers,
    )
    assert finished.status_code == 400

    live = add_match(season, division, teams["A"], teams["B"], org_id=org.id, status="In Progress")
    stranger = Player(organization_id=org.id, team_id=teams["C"].id, full_name="Odd",
                      jersey_number="9", status="Active", created_by=org.id, updated_by=org.id)
    dbsession.add(stranger)
    dbsession.commit()
    dbsession.refresh(stranger)

    foreign = client.post(
        f"/api/v1/matches/{live.id}/stats/live",
        json={"player_id": str(stranger.id), "points": 1}, headers=headers,
    )
    assert foreign.status_code == 400


def test_foul_limit_setting(client, dbsession, org, admin):
    headers = _admin_headers(client, admin)
    res = client.put("/api/v1/settings/foul-limit", json={"foul_limit": 3}, headers=headers)
    assert res.status_code == 200

    pub = client.get("/api/v1/settings/public/foul-limit")
    assert pub.status_code == 200
    assert pub.json()["foul_limit"] == 3
