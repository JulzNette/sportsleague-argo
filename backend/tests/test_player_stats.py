"""
Per-match player stats entry and the aggregated player leaderboard.
"""
import pytest

from app.core.security import hash_password
from app.models.player import Player
from app.models.stub import User


@pytest.fixture()
def admin(dbsession, org):
    user = User(
        organization_id=org.id,
        email="admin@example.com",
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
        Player(organization_id=org.id, team_id=teams["A"].id, full_name="Ann Player",
               jersey_number="1", status="Active", created_by=org.id, updated_by=org.id),
        Player(organization_id=org.id, team_id=teams["A"].id, full_name="Ben Player",
               jersey_number="2", status="Active", created_by=org.id, updated_by=org.id),
        Player(organization_id=org.id, team_id=teams["B"].id, full_name="Cara Player",
               jersey_number="3", status="Active", created_by=org.id, updated_by=org.id),
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


def test_player_stats_flow(client, dbsession, org, season_division_teams, players, add_match, admin):
    season, division, teams = season_division_teams
    match = add_match(season, division, teams["A"], teams["B"], org_id=org.id, home_score=70, away_score=65)
    headers = _admin_headers(client, admin)

    before = client.get(f"/api/v1/matches/{match.id}/stats", headers=headers)
    assert before.status_code == 200 and before.json() == []

    payload = {"lines": [
        {"player_id": str(players[0].id), "points": 24, "assists": 6, "fouls": 2, "rebounds": 8, "steals": 1},
        {"player_id": str(players[1].id), "points": 10, "assists": 3, "fouls": 1, "rebounds": 4, "steals": 0},
        {"player_id": str(players[2].id), "points": 20, "assists": 4, "fouls": 3, "rebounds": 6, "steals": 2},
    ]}
    created = client.post(f"/api/v1/matches/{match.id}/stats", json=payload, headers=headers)
    assert created.status_code == 201
    assert len(created.json()) == 3

    fetched = client.get(f"/api/v1/matches/{match.id}/stats", headers=headers)
    assert fetched.status_code == 200
    by_name = {row["player_name"]: row for row in fetched.json()}
    assert by_name["Ann Player"]["points"] == 24
    assert by_name["Ann Player"]["team_name"] == "Team A"
    assert by_name["Cara Player"]["team_name"] == "Team B"

    # Replacing overwrites, not duplicates.
    again = client.post(f"/api/v1/matches/{match.id}/stats", json=payload, headers=headers)
    assert again.status_code == 201
    fetched2 = client.get(f"/api/v1/matches/{match.id}/stats", headers=headers)
    assert len(fetched2.json()) == 3

    agg = client.get("/api/v1/stats/players", params={"season_id": str(season.id)}, headers=headers)
    assert agg.status_code == 200
    rows = {r["player_name"]: r for r in agg.json()}
    assert rows["Ann Player"]["points"] == 24
    assert rows["Ann Player"]["games_played"] == 1
    assert rows["Ann Player"]["rank"] == 1


def test_player_stats_rejects_foreign_player(client, dbsession, org, season_division_teams, players, add_match, admin):
    season, division, teams = season_division_teams
    match = add_match(season, division, teams["A"], teams["B"], org_id=org.id, home_score=70, away_score=65)
    headers = _admin_headers(client, admin)

    stranger = Player(organization_id=org.id, team_id=teams["C"].id, full_name="Odd One Out",
                      jersey_number="9", status="Active", created_by=org.id, updated_by=org.id)
    dbsession.add(stranger)
    dbsession.commit()
    dbsession.refresh(stranger)

    res = client.post(f"/api/v1/matches/{match.id}/stats", json={"lines": [
        {"player_id": str(stranger.id), "points": 1},
    ]}, headers=headers)
    assert res.status_code == 400


def test_player_stats_requires_completed_match(client, dbsession, org, season_division_teams, players, add_match, admin):
    season, division, teams = season_division_teams
    match = add_match(season, division, teams["A"], teams["B"], org_id=org.id, status="Scheduled")
    headers = _admin_headers(client, admin)

    res = client.post(f"/api/v1/matches/{match.id}/stats", json={"lines": [
        {"player_id": str(players[0].id), "points": 1},
    ]}, headers=headers)
    assert res.status_code == 400


def test_viewer_cannot_enter_stats(client, dbsession, org, season_division_teams, players, add_match):
    season, division, teams = season_division_teams
    match = add_match(season, division, teams["A"], teams["B"], org_id=org.id, home_score=70, away_score=65)

    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Read Only", "email": "ro.stat@example.com", "password": "password123",
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    res = client.post(f"/api/v1/matches/{match.id}/stats", json={"lines": [
        {"player_id": str(players[0].id), "points": 1},
    ]}, headers=headers)
    assert res.status_code == 403
