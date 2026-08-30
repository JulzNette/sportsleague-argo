"""
Team edit access: the Team Manager manages their roster but cannot edit team
details (name/division/status/contact) - that's league-admin-only now.
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


def test_team_manager_cannot_edit_team(client, dbsession, org, season_division_teams):
    admin = _make_user(dbsession, org, "admin.team@example.com", "System Administrator")
    manager = _make_user(dbsession, org, "manager.team@example.com", "Team Manager")
    admin_headers = _login(client, admin.email)
    manager_headers = _login(client, manager.email)
    _, division, _ = season_division_teams

    # Manager registers a team that gets approved.
    reg = client.post("/api/v1/registrations", json={
        "team_name": "Team TM",
        "coach_name": "Coach X",
        "players": [{"full_name": "P1", "jersey_number": "1"}],
        "division_id": str(division.id),
    }, headers=manager_headers)
    review = client.patch(f"/api/v1/registrations/{reg.json()['id']}/review",
                          json={"status": "Approved", "review_comment": "ok"}, headers=admin_headers)
    assert review.status_code == 200

    team = next(t for t in client.get("/api/v1/teams", headers=manager_headers).json() if t["name"] == "Team TM")

    # Editing team details is denied for the Team Manager.
    res = client.patch(f"/api/v1/teams/{team['id']}", json={"name": "Renamed"}, headers=manager_headers)
    assert res.status_code == 403
