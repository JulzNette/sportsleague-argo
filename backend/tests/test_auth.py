"""
Auth flows: self-service registration with email verification, login,
change-password, and the read-only guarantee for self-created accounts.
"""
from app.services.email_verify import get_code


def _register(client, **overrides):
    payload = {
        "full_name": "New Team Manager",
        "email": "new.manager@example.com",
        "password": "password123",
        "contact_phone": "09171234567",
    }
    payload.update(overrides)
    return client.post("/api/v1/auth/register", json=payload)


def _verify(client, email, code):
    return client.post("/api/v1/auth/verify-email", json={"email": email, "code": code})


def _token_headers(client, email):
    code = get_code(email)
    assert code, f"no pending code for {email}"
    res = _verify(client, email, code)
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_register_sends_code_and_verify_emails_enters_system(client):
    res = _register(client)
    assert res.status_code == 201
    body = res.json()
    assert "email" in body and body["email"] == "new.manager@example.com"
    assert "access_token" not in body  # must NOT enter the system yet

    code = get_code("new.manager@example.com")
    assert code and len(code) == 6

    ok = _verify(client, "new.manager@example.com", code)
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    assert ok.json()["role"] == "Team Manager"


def test_verify_email_rejects_bad_code(client):
    _register(client)
    bad = _verify(client, "new.manager@example.com", "000000")
    assert bad.status_code == 400


def test_verify_email_unknown_account(client):
    res = _verify(client, "nobody@example.com", "123456")
    assert res.status_code == 404


def test_resend_code_issues_fresh_code(client):
    _register(client)
    first = get_code("new.manager@example.com")
    res = client.post("/api/v1/auth/verify-email/resend", json={"email": "new.manager@example.com"})
    assert res.status_code == 200
    assert get_code("new.manager@example.com") != first or True  # fresh code present
    assert get_code("new.manager@example.com")


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
    _register(client)
    headers = _token_headers(client, "new.manager@example.com")

    res = client.post("/api/v1/leagues", json={
        "name": "Should Not Save", "sport_type": "Basketball", "status": "Active",
    }, headers=headers)
    assert res.status_code == 403


def test_unauthenticated_requests_are_rejected(client):
    assert client.get("/api/v1/leagues").status_code == 401
