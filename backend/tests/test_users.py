"""
Superadmin User Management: list/create/update/reset-password/deactivate users,
plus RBAC gating so a non-admin role cannot touch user management.
"""
from app.core.security import hash_password
from app.models.stub import User


def _make_user(dbsession, org, *, email, full_name="Test User", role="Viewer", active=True):
    user = User(
        organization_id=org.id, email=email, hashed_password=hash_password("Admin123"),
        full_name=full_name, role=role, is_active=active,
    )
    dbsession.add(user)
    dbsession.commit()
    dbsession.refresh(user)
    return user


def _login(client, email):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Admin123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_superadmin_can_list_create_and_edit_users(client, dbsession, org):
    sa = _make_user(dbsession, org, email="sa@example.com", role="Superadmin")
    _make_user(dbsession, org, email="viewer@example.com", full_name="A Viewer", role="Viewer")
    headers = _login(client, "sa@example.com")

    listed = client.get("/api/v1/users", headers=headers)
    assert listed.status_code == 200
    emails = [u["email"] for u in listed.json()]
    assert "sa@example.com" in emails and "viewer@example.com" in emails

    created = client.post("/api/v1/users", json={
        "full_name": "New Referee", "email": "new.ref@example.com",
        "password": "password123", "role": "Referee",
    }, headers=headers)
    assert created.status_code == 201
    created_id = created.json()["id"]

    updated = client.patch(f"/api/v1/users/{created_id}", json={"role": "Season Manager"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["role"] == "Season Manager"

    reset = client.post(f"/api/v1/users/{created_id}/reset-password", json={"password": "brandnew123"}, headers=headers)
    assert reset.status_code == 204

    # User could log in with the new password and new role.
    relogin = client.post("/api/v1/auth/login", json={"email": "new.ref@example.com", "password": "brandnew123"})
    assert relogin.status_code == 200
    assert relogin.json()["role"] == "Season Manager"


def test_system_administrator_cannot_manage_users(client, dbsession, org):
    sa = _make_user(dbsession, org, email="other.sa@example.com", role="Superadmin")
    sysadmin = _make_user(dbsession, org, email="sysadmin@example.com", role="System Administrator")
    sys_headers = _login(client, "sysadmin@example.com")

    # System Administrator cannot view or manage user accounts (Superadmin only).
    assert client.get("/api/v1/users", headers=sys_headers).status_code == 403
    assert client.post("/api/v1/users", json={
        "full_name": "Nope", "email": "nope@example.com", "password": "password123", "role": "Viewer",
    }, headers=sys_headers).status_code == 403

    db_sa = dbsession.query(User).filter(User.email == "other.sa@example.com").first()
    assert client.patch(f"/api/v1/users/{db_sa.id}", json={"is_active": False}, headers=sys_headers).status_code == 403
    assert client.delete(f"/api/v1/users/{db_sa.id}", headers=sys_headers).status_code == 403


def test_deactivate_blocks_login_but_keeps_row(client, dbsession, org):
    sa = _make_user(dbsession, org, email="deact.sa@example.com", role="Superadmin")
    victim = _make_user(dbsession, org, email="victim@example.com", full_name="Victim", role="Player")
    headers = _login(client, "deact.sa@example.com")

    res = client.delete(f"/api/v1/users/{victim.id}", headers=headers)
    assert res.status_code == 204

    assert client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": "Admin123"}).status_code == 401
    dbsession.expire_all()
    refreshed = dbsession.query(User).filter(User.id == victim.id).first()
    assert refreshed.is_active is False


def test_non_admin_cannot_access_user_management(client, dbsession, org):
    _make_user(dbsession, org, email="plain@example.com", role="Player")
    headers = _login(client, "plain@example.com")
    assert client.get("/api/v1/users", headers=headers).status_code == 403
