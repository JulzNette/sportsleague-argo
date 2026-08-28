"""
Auth flows: self-service registration, login, change-password, and the
read-only guarantee for self-created accounts.
"""


def test_register_creates_team_manager_account(client):
    res = client.post("/api/v1/auth/register", json={
        "full_name": "New Team Manager", "email": "new.manager@example.com", "password": "password123",
        "contact_phone": "09171234567",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["role"] == "Team Manager"


def test_register_rejects_duplicate_email(client):
    payload = {"full_name": "Dup User", "email": "dup@example.com", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_round_trip(client):
    client.post("/api/v1/auth/register", json={
        "full_name": "Login User", "email": "login.user@example.com", "password": "password123",
    })
    ok = client.post("/api/v1/auth/login", json={"email": "LOGIN.USER@example.com", "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    bad = client.post("/api/v1/auth/login", json={"email": "login.user@example.com", "password": "wrong"})
    assert bad.status_code == 401


def test_change_password_updates_credentials(client):
    client.post("/api/v1/auth/register", json={
        "full_name": "PW User", "email": "pw.user@example.com", "password": "password123",
    })
    login = client.post("/api/v1/auth/login", json={"email": "pw.user@example.com", "password": "password123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    wrong = client.post("/api/v1/auth/change-password", json={
        "current_password": "not-my-password", "new_password": "newpassword123",
    }, headers=headers)
    assert wrong.status_code == 400

    short = client.post("/api/v1/auth/change-password", json={
        "current_password": "password123", "new_password": "short",
    }, headers=headers)
    assert short.status_code == 422

    ok = client.post("/api/v1/auth/change-password", json={
        "current_password": "password123", "new_password": "newpassword123",
    }, headers=headers)
    assert ok.status_code == 204

    old = client.post("/api/v1/auth/login", json={"email": "pw.user@example.com", "password": "password123"})
    assert old.status_code == 401
    fresh = client.post("/api/v1/auth/login", json={"email": "pw.user@example.com", "password": "newpassword123"})
    assert fresh.status_code == 200


def test_change_password_requires_auth(client):
    res = client.post("/api/v1/auth/change-password", json={
        "current_password": "password123", "new_password": "newpassword123",
    })
    assert res.status_code == 401


def test_team_manager_cannot_write_admin_data(client):
    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Read Only", "email": "readonly@example.com", "password": "password123",
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    res = client.post("/api/v1/leagues", json={
        "name": "Should Not Save", "sport_type": "Basketball", "status": "Active",
    }, headers=headers)
    assert res.status_code == 403


def test_unauthenticated_requests_are_rejected(client):
    assert client.get("/api/v1/leagues").status_code == 401
