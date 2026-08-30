"""
Superadmin portal summary: org-wide counts, registration pipeline, and user
role distribution - only accessible to the Superadmin role.
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


def test_superadmin_can_read_superadmin_summary(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "superadmin.portal@example.com", "Superadmin")
    headers = _login(client, "superadmin.portal@example.com")

    res = client.get("/api/v1/superadmin/summary", headers=headers)

    assert res.status_code == 200
    body = res.json()
    counts = body["counts"]
    assert counts["leagues"] == 1
    assert counts["seasons"] == 1
    assert counts["divisions"] == 1
    assert counts["teams"] == 4
    assert counts["users"] == 1
    assert body["registrations"]["pending"] == 0
    assert body["users_by_role"].get("Superadmin") == 1


def test_system_administrator_cannot_read_superadmin_summary(client, dbsession, org):
    _make_user(dbsession, org, "sysadmin.portal@example.com", "System Administrator")
    headers = _login(client, "sysadmin.portal@example.com")

    res = client.get("/api/v1/superadmin/summary", headers=headers)

    assert res.status_code == 403
