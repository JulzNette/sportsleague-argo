"""
Coach records CRUD: create/list/update/delete scoped to the org, with exactly
one coach per team (conflict -> 409) and sane role-based access.
"""
import pytest

from app.core.security import hash_password
from app.models.stub import User


@pytest.fixture()
def admin(dbsession, org):
    user = User(
        organization_id=org.id,
        email="admin.coach@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin",
        role="System Administrator",
        is_active=True,
    )
    dbsession.add(user)
    dbsession.commit()
    dbsession.refresh(user)
    return user


def _admin_headers(client, admin):
    login = client.post("/api/v1/auth/login", json={"email": admin.email, "password": "adminpass123"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_coach_crud_flow(client, dbsession, org, season_division_teams, admin):
    _, _, teams = season_division_teams
    headers = _admin_headers(client, admin)
    team_a = teams["A"]

    created = client.post("/api/v1/coaches", json={
        "team_id": str(team_a.id),
        "full_name": "Coach Cardo",
        "role": "Head Coach",
        "email": "cardo@example.com",
        "phone": "0917",
        "credentials": "FIBA Level 1",
    }, headers=headers)
    assert created.status_code == 201
    coach = created.json()
    assert coach["full_name"] == "Coach Cardo"
    assert coach["team_name"] == "Team A"
    coach_id = coach["id"]

    # Duplicate coach for the same team is rejected (one head coach per team).
    dup = client.post("/api/v1/coaches", json={
        "team_id": str(team_a.id), "full_name": "Second Coach",
    }, headers=headers)
    assert dup.status_code == 409

    # A coach may be attached to another team.
    other = client.post("/api/v1/coaches", json={
        "team_id": str(teams["B"].id), "full_name": "Coach B",
    }, headers=headers)
    assert other.status_code == 201

    listed = client.get("/api/v1/coaches", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    updated = client.patch(f"/api/v1/coaches/{coach_id}", json={"status": "Inactive"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "Inactive"

    # Soft delete removes it from the active list.
    deleted = client.delete(f"/api/v1/coaches/{coach_id}", headers=headers)
    assert deleted.status_code == 204
    after = client.get("/api/v1/coaches", headers=headers)
    assert len(after.json()) == 1


def test_viewer_cannot_manage_coaches(client, dbsession, org, season_division_teams):
    _, _, teams = season_division_teams
    client.post("/api/v1/auth/register", json={
        "full_name": "Read Only", "email": "ro.coach@example.com", "password": "password123",
    })
    from app.services.email_verify import get_code
    verify = client.post("/api/v1/auth/verify-email", json={
        "email": "ro.coach@example.com", "code": get_code("ro.coach@example.com"),
    })
    assert verify.status_code == 200
    headers = {"Authorization": f"Bearer {verify.json()['access_token']}"}

    res = client.post("/api/v1/coaches", json={
        "team_id": str(teams["A"].id), "full_name": "Blocked",
    }, headers=headers)
    assert res.status_code == 403


def _make_user(dbsession, org, email, role):
    from app.core.security import hash_password
    user = User(
        organization_id=org.id, email=email, hashed_password=hash_password("Admin123"),
        full_name=role, role=role, is_active=True,
    )
    dbsession.add(user)
    dbsession.commit()
    return user


def _login_headers(client, email):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Admin123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _approve(
    client, reviewer_headers, division_id, *, manager_headers, team_name,
    coach_name="Coach M", coach_email="m@example.com", coach_phone="0917111",
):
    payload = {
        "team_name": team_name,
        "coach_name": coach_name,
        "contact_email": coach_email,
        "contact_phone": coach_phone,
        "players": [{"full_name": "P1", "jersey_number": "1"}],
    }
    reg = client.post("/api/v1/registrations", json={**payload, "division_id": str(division_id)}, headers=manager_headers)
    assert reg.status_code == 201
    review = client.patch(
        f"/api/v1/registrations/{reg.json()['id']}/review",
        json={"status": "Approved", "review_comment": "ok"},
        headers=reviewer_headers,
    )
    assert review.status_code == 200


def test_team_manager_manages_only_their_own_team_coach(
    client, dbsession, org, season_division_teams,
):
    admin = _make_user(dbsession, org, "admin.tm@example.com", "System Administrator")
    manager = _make_user(dbsession, org, "manager.coach@example.com", "Team Manager")
    admin_headers = _login_headers(client, admin.email)
    manager_headers = _login_headers(client, manager.email)
    _, division, _ = season_division_teams

    # Manager registers a team; approval auto-creates their coach and team.
    _approve(client, admin_headers, division.id, manager_headers=manager_headers, team_name="My Lions")

    my_team = next(t for t in client.get("/api/v1/teams", headers=manager_headers).json() if t["name"] == "My Lions")

    # Manager sees only their own team's coach.
    coach_list = client.get("/api/v1/coaches", headers=manager_headers).json()
    assert len(coach_list) == 1
    assert coach_list[0]["team_id"] == my_team["id"]
    own_coach = coach_list[0]
    assert own_coach["full_name"] == "Coach M"

    # Manager can update their own coach.
    upd = client.patch(f"/api/v1/coaches/{own_coach['id']}", json={"full_name": "Coach M Updated"}, headers=manager_headers)
    assert upd.status_code == 200
    assert upd.json()["full_name"] == "Coach M Updated"

    # Manager cannot add a coach to another team they do not own.
    other = next(t for t in client.get("/api/v1/teams", headers=admin_headers).json() if t["name"] == "Team A")
    blocked = client.post("/api/v1/coaches", json={
        "team_id": str(other["id"]), "full_name": "Sneaky",
    }, headers=manager_headers)
    assert blocked.status_code == 403
