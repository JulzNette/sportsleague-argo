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


def test_manager_sees_only_own_team_and_can_login_own_players(
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

    # The manager sees ONLY their own team's players...
    players = client.get("/api/v1/players", headers=manager_headers).json()
    names = {p["full_name"] for p in players}
    assert "Mine" in names
    assert "Rival" not in names

    # ...and every visible player allows creating a login.
    assert all(p["login_allowed"] is True for p in players)

    # Admins still see players across all teams and can create logins for all.
    admin_players = client.get("/api/v1/players", headers=admin_headers).json()
    admin_names = {p["full_name"] for p in admin_players}
    assert {"Mine", "Rival"} <= admin_names
    assert all(p["login_allowed"] is True for p in admin_players)


def test_player_account_sees_only_own_team_mates(client, dbsession, org, season_division_teams):
    """A Player-role login created for a roster member is scoped to their team:
    they only see their own team mates on the players list, not other teams."""
    admin = _make_user(dbsession, org, "admin.scope@example.com", "System Administrator")
    admin_headers = _login(client, admin.email)
    _, division, teams = season_division_teams
    team_a = teams["A"]
    team_b = teams["B"]

    # Two players on team A and one on team B.
    mine1 = _add_player(client, admin_headers, team_a.id, "Teammate One", "11")
    _add_player(client, admin_headers, team_a.id, "Teammate Two", "12")
    _add_player(client, admin_headers, team_b.id, "Outsider", "21")

    # Create a Player-role login for one of team A's players.
    created = client.post(f"/api/v1/players/{mine1['id']}/account", json={
        "email": "teammate.one@example.com", "password": "password123",
    }, headers=admin_headers)
    assert created.status_code == 201

    login = client.post("/api/v1/auth/login", json={"email": "teammate.one@example.com", "password": "password123"})
    assert login.status_code == 200
    player_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # The Player-role account sees only team A's players (its own team mates).
    players = client.get("/api/v1/players", headers=player_headers).json()
    names = {p["full_name"] for p in players}
    assert names == {"Teammate One", "Teammate Two"}
    assert "Outsider" not in names

    # They cannot view a player from another team directly either.
    outsider = next(p for p in client.get("/api/v1/players", headers=admin_headers).json() if p["full_name"] == "Outsider")
    assert client.get(f"/api/v1/players/{outsider['id']}", headers=player_headers).status_code == 403
