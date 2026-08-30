"""
Player login accounts: a Team Manager creates a Player-role login for a roster
member on their own team; admins can create for anyone. The account logs in with
the view-only Player role, and a Team Manager cannot create accounts for another
team's players.
"""
from app.core.security import hash_password
from app.models.stub import User


def _make_user(dbsession, org, email, role):
    user = User(
        organization_id=org.id, email=email, hashed_password=hash_password("Admin123"),
        full_name=role, role=role, is_active=True,
    )
    dbsession.add(user)
    dbsession.commit()
    return user


def _login(client, email):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Admin123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _approve_team_for_manager(client, admin_headers, division_id, manager_headers, team_name):
    reg = client.post("/api/v1/registrations", json={
        "team_name": team_name,
        "coach_name": "Coach X",
        "players": [{"full_name": "P1", "jersey_number": "1"}],
        "division_id": str(division_id),
    }, headers=manager_headers)
    assert reg.status_code == 201
    review = client.patch(
        f"/api/v1/registrations/{reg.json()['id']}/review",
        json={"status": "Approved", "review_comment": "ok"},
        headers=admin_headers,
    )
    assert review.status_code == 200


def _add_player(client, headers, team_id, name, jersey):
    res = client.post("/api/v1/players", json={
        "team_id": str(team_id), "full_name": name, "jersey_number": jersey,
    }, headers=headers)
    assert res.status_code == 201
    return res.json()


def test_team_manager_creates_player_account(client, dbsession, org, season_division_teams):
    admin = _make_user(dbsession, org, "admin.tm@example.com", "System Administrator")
    manager = _make_user(dbsession, org, "manager.login@example.com", "Team Manager")
    admin_headers = _login(client, admin.email)
    manager_headers = _login(client, manager.email)
    _, division, _ = season_division_teams

    _approve_team_for_manager(client, admin_headers, division.id, manager_headers, "Lions")
    my_team = next(t for t in client.get("/api/v1/teams", headers=manager_headers).json() if t["name"] == "Lions")
    player = _add_player(client, manager_headers, my_team["id"], "John Doe", "10")

    created = client.post(f"/api/v1/players/{player['id']}/account", json={
        "email": "john.doe@example.com", "password": "password123",
    }, headers=manager_headers)
    assert created.status_code == 201
    assert created.json()["role"] == "Player"
    assert created.json()["full_name"] == "John Doe"

    # The new player account can log in with the Player (view-only) role.
    login = client.post("/api/v1/auth/login", json={"email": "john.doe@example.com", "password": "password123"})
    assert login.status_code == 200
    assert login.json()["role"] == "Player"


def test_team_manager_cannot_create_login_for_other_team(client, dbsession, org, season_division_teams):
    admin = _make_user(dbsession, org, "admin.filter@example.com", "System Administrator")
    manager = _make_user(dbsession, org, "manager.filter@example.com", "Team Manager")
    admin_headers = _login(client, admin.email)
    manager_headers = _login(client, manager.email)
    _, division, teams = season_division_teams

    _approve_team_for_manager(client, admin_headers, division.id, manager_headers, "Lions")

    other = next(t for t in teams.values() if t.name != "Lions")
    other_player = client.post("/api/v1/players", json={
        "team_id": str(other.id), "full_name": "Rival", "jersey_number": "2",
    }, headers=admin_headers).json()

    blocked = client.post(f"/api/v1/players/{other_player['id']}/account", json={
        "email": "rival@example.com", "password": "password123",
    }, headers=manager_headers)
    assert blocked.status_code == 403


def test_duplicate_email_is_rejected(client, dbsession, org, season_division_teams):
    admin = _make_user(dbsession, org, "admin.dup@example.com", "Superadmin")
    admin_headers = _login(client, admin.email)
    _, _, teams = season_division_teams
    team_a = teams["A"]
    player = _add_player(client, admin_headers, team_a.id, "Dup Player", "7")

    first = client.post(f"/api/v1/players/{player['id']}/account", json={
        "email": "dup@example.com", "password": "password123",
    }, headers=admin_headers)
    assert first.status_code == 201

    second = client.post(f"/api/v1/players/{player['id']}/account", json={
        "email": "dup@example.com", "password": "password123",
    }, headers=admin_headers)
    assert second.status_code == 409


def test_manager_sees_all_players_but_login_allowed_only_for_own_team(
    client, dbsession, org, season_division_teams
):
    admin = _make_user(dbsession, org, "admin.all@example.com", "System Administrator")
    manager = _make_user(dbsession, org, "manager.all@example.com", "Team Manager")
    admin_headers = _login(client, admin.email)
    manager_headers = _login(client, manager.email)
    _, division, teams = season_division_teams

    _approve_team_for_manager(client, admin_headers, division.id, manager_headers, "Lions")
    my_team = next(t for t in client.get("/api/v1/teams", headers=manager_headers).json() if t["name"] == "Lions")

    # Manager's own-team player plus a player on a different team.
    mine = _add_player(client, manager_headers, my_team["id"], "Mine", "5")
    other = next(t for t in teams.values() if t.name != "Lions")
    _add_player(client, admin_headers, other.id, "Rival", "6")

    # The manager sees players across ALL teams...
    players = client.get(f"/api/v1/players", headers=manager_headers).json()
    assert {p["full_name"] for p in players} >= {"Mine", "Rival"}

    # ...but login_allowed is only true for their own team's player.
    by_name = {p["full_name"]: p for p in players}
    assert by_name["Mine"]["login_allowed"] is True
    assert by_name["Rival"]["login_allowed"] is False
