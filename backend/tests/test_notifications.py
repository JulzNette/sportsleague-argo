"""
In-app notifications for the registration workflow: reviewers are notified
when someone submits, and the submitter is notified of the approval/rejection
outcome.
"""

from app.core.security import hash_password
from app.models.stub import User

PAYLOAD = {
    "team_name": "Silver Sharks",
    "coach_name": "Nina Ramos",
    "contact_email": "nina@example.com",
    "contact_phone": "09171234567",
    "players": [
        {"full_name": "Jules Aquino", "jersey_number": "7", "position": "Guard"},
        {"full_name": "Bea Navarro", "jersey_number": "11", "position": "Forward"},
    ],
    "documents": [
        {"player_full_name": "Jules Aquino", "document_type": "Birth Certificate", "file_name": "jules.pdf"},
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


def _register_viewer(client, email):
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Viewer", "email": email, "password": "password123",
    })
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _submit(client, headers, division_id, team_name="Silver Sharks"):
    return client.post(
        "/api/v1/registrations",
        json={**PAYLOAD, "division_id": str(division_id), "team_name": team_name},
        headers=headers,
    )


def test_submission_notifies_reviewers(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.alert@example.com", "League Administrator")
    _make_user(dbsession, org, "manager.alert@example.com", "Season Manager")
    reviewer = _login(client, "admin.alert@example.com")
    submitter = _register_viewer(client, "viewer.alert@example.com")
    _, division, _ = season_division_teams

    res = _submit(client, submitter, division.id)
    assert res.status_code == 201

    for headers in (reviewer, _login(client, "manager.alert@example.com")):
        notifications = client.get("/api/v1/notifications", headers=headers).json()
        assert len(notifications) == 1
        note = notifications[0]
        assert note["type"] == "registration.submitted"
        assert note["title"] == "New registration: Silver Sharks"
        assert note["registration_id"] == res.json()["id"]
        assert note["is_read"] is False


def test_submitter_gets_no_notification_for_own_submission(client, season_division_teams):
    submitter = _register_viewer(client, "viewer.own@example.com")
    _, division, _ = season_division_teams
    _submit(client, submitter, division.id)

    notifications = client.get("/api/v1/notifications", headers=submitter).json()
    assert notifications == []


def test_approval_notifies_submitter(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.decision@example.com", "League Administrator")
    admin = _login(client, "admin.decision@example.com")
    submitter = _register_viewer(client, "viewer.decision@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, submitter, division.id).json()["id"]

    res = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Approved", "review_comment": "Welcome!"},
        headers=admin,
    )
    assert res.status_code == 200

    notifications = client.get("/api/v1/notifications", headers=submitter).json()
    assert len(notifications) == 1
    note = notifications[0]
    assert note["type"] == "registration.approved"
    assert note["registration_id"] == reg_id


def test_rejection_notifies_submitter(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.deny@example.com", "Season Manager")
    admin = _login(client, "admin.deny@example.com")
    submitter = _register_viewer(client, "viewer.deny@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, submitter, division.id).json()["id"]

    res = client.patch(
        f"/api/v1/registrations/{reg_id}/review",
        json={"status": "Rejected", "review_comment": "Roster below minimum."},
        headers=admin,
    )
    assert res.status_code == 200

    notifications = client.get("/api/v1/notifications", headers=submitter).json()
    assert notifications[0]["type"] == "registration.rejected"


def test_unread_count_and_mark_read(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.unread@example.com", "League Administrator")
    admin = _login(client, "admin.unread@example.com")
    submitter = _register_viewer(client, "viewer.unread@example.com")
    _, division, _ = season_division_teams
    _submit(client, submitter, division.id, team_name="Team Unread One")
    _submit(client, submitter, division.id, team_name="Team Unread Two")

    count = client.get("/api/v1/notifications/unread-count", headers=admin).json()
    assert count["count"] == 2

    note_ids = [n["id"] for n in client.get("/api/v1/notifications", headers=admin).json()]
    assert len(note_ids) == 2
    marked = client.patch(f"/api/v1/notifications/{note_ids[0]}/read", headers=admin)
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
    assert client.get("/api/v1/notifications/unread-count", headers=admin).json()["count"] == 1

    _submit(client, submitter, division.id, team_name="Team Unread Three")
    assert client.get("/api/v1/notifications/unread-count", headers=admin).json()["count"] == 2
    cleared = client.post("/api/v1/notifications/read-all", headers=admin)
    assert cleared.status_code == 200
    assert client.get("/api/v1/notifications/unread-count", headers=admin).json()["count"] == 0
