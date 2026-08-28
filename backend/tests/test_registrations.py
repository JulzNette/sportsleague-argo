"""
League registration workflow: submitting a registration, reviewer-only
approval/rejection, and the side-effect of approval (auto-creating the Team
and its Players in the applied-for division).
"""

from app.core.security import hash_password
from app.models.stub import User

PAYLOAD = {
    "team_name": "Silver Sharks",
    "coach_name": "Nina Ramos",
    "contact_email": "nina@example.com",
    "contact_phone": "09171234567",
    "registration_fee": 1.0,
    "notes": "New team hoping to join.",
    "players": [
        {"full_name": "Jules Aquino", "jersey_number": "7", "position": "Guard",
         "date_of_birth": "2003-05-12", "contact_phone": "09171112222"},
        {"full_name": "Bea Navarro", "jersey_number": "11", "position": "Forward"},
    ],
    "documents": [
        {"player_full_name": "Jules Aquino", "document_type": "Birth Certificate", "file_name": "jules.pdf"},
        {"document_type": "Team Waiver", "file_name": "waiver.pdf"},
    ],
}


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


def _register_viewer(client, dbsession, org, email):
    """Create a Team Manager account and return auth headers."""
    user = User(
        organization_id=org.id, email=email, hashed_password=hash_password("Admin123"),
        full_name="Team Manager", role="Team Manager", is_active=True,
    )
    dbsession.add(user)
    dbsession.commit()
    return _login(client, email)


def _submit(client, headers, division_id, **overrides):
    payload = {**PAYLOAD, "division_id": str(division_id), **overrides}
    return client.post("/api/v1/registrations", json=payload, headers=headers)


def test_any_user_can_submit_registration(client, dbsession, org, season_division_teams):
    _, division, _ = season_division_teams
    headers = _register_viewer(client, dbsession, org, "viewer.submit@example.com")

    res = _submit(client, headers, division.id)

    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "Pending"
    assert body["team_name"] == "Silver Sharks"
    assert len(body["players"]) == 2
    assert len(body["documents"]) == 2


def test_approval_creates_team_and_players(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.approve@example.com", "League Administrator")
    headers = _login(client, "admin.approve@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id).json()["id"]

    res = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Approved", "review_comment": "Welcome aboard!"},
        headers=headers,
    )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "Approved"
    assert body["review_comment"] == "Welcome aboard!"

    teams = client.get("/api/v1/teams", headers=headers).json()
    team = next(t for t in teams if t["name"] == "Silver Sharks")
    assert team["division_id"] == str(division.id)

    players = client.get("/api/v1/players", params={"team_id": team["id"]}, headers=headers).json()
    assert {p["full_name"] for p in players} == {"Jules Aquino", "Bea Navarro"}


def test_rejection_does_not_create_team(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.reject@example.com", "Season Manager")
    headers = _login(client, "admin.reject@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id).json()["id"]

    res = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Rejected", "review_comment": "Roster below minimum."},
        headers=headers,
    )

    assert res.status_code == 200
    assert res.json()["status"] == "Rejected"
    teams = client.get("/api/v1/teams", headers=headers).json()
    assert not any(t["name"] == "Silver Sharks" for t in teams)


def test_review_requires_review_permission(client, dbsession, org, season_division_teams):
    _, division, _ = season_division_teams
    headers = _register_viewer(client, dbsession, org, "viewer.review@example.com")
    reg_id = _submit(client, headers, division.id).json()["id"]

    res = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Approved", "review_comment": ""},
        headers=headers,
    )

    assert res.status_code == 403


def test_cannot_review_twice(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.twice@example.com", "System Administrator")
    headers = _login(client, "admin.twice@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id).json()["id"]

    first = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Approved", "review_comment": "Ok"},
        headers=headers,
    )
    assert first.status_code == 200

    second = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Rejected", "review_comment": "Changed our minds"},
        headers=headers,
    )
    assert second.status_code == 400


def test_non_reviewer_only_sees_own_registrations(client, dbsession, org, season_division_teams):
    _, division, _ = season_division_teams
    viewer_a = _register_viewer(client, dbsession, org, "viewer.a@example.com")
    viewer_b = _register_viewer(client, dbsession, org, "viewer.b@example.com")

    _submit(client, viewer_a, division.id, team_name="Team Alpha")
    _submit(client, viewer_b, division.id, team_name="Team Beta")

    mine = client.get("/api/v1/registrations", headers=viewer_a).json()
    assert {r["team_name"] for r in mine} == {"Team Alpha"}


def test_reviewer_sees_all_registrations(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.all@example.com", "League Administrator")
    reviewer = _login(client, "admin.all@example.com")
    viewer = _register_viewer(client, dbsession, org, "viewer.c@example.com")
    _, division, _ = season_division_teams

    _submit(client, reviewer, division.id, team_name="Team One")
    _submit(client, viewer, division.id, team_name="Team Two")

    all_regs = client.get("/api/v1/registrations", headers=reviewer).json()
    assert {r["team_name"] for r in all_regs} == {"Team One", "Team Two"}
