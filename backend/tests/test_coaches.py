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
    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Read Only", "email": "ro.coach@example.com", "password": "password123",
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    res = client.post("/api/v1/coaches", json={
        "team_id": str(teams["A"].id), "full_name": "Blocked",
    }, headers=headers)
    assert res.status_code == 403
