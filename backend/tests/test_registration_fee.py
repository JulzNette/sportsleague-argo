"""
Registration fee + payment: the registrant types a fee, it is stored, an admin
can mark it Paid, and the admin can email the registrant (simulated in tests).
"""
import logging

from app.core.security import hash_password
from app.models.stub import User

PAYLOAD = {
    "team_name": "Silver Sharks",
    "coach_name": "Nina Ramos",
    "contact_email": "nina@example.com",
    "contact_phone": "09171234567",
    "registration_fee": 1.0,
    "notes": "Fee is one peso for the demo.",
    "players": [
        {"full_name": "Jules Aquino", "jersey_number": "7", "position": "Guard"},
        {"full_name": "Bea Navarro", "jersey_number": "11", "position": "Forward"},
    ],
    "documents": [],
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


def _submit(client, headers, division_id, **overrides):
    payload = {**PAYLOAD, "division_id": str(division_id), **overrides}
    return client.post("/api/v1/registrations", json=payload, headers=headers)


def test_registration_saves_fee_and_defaults_payment_to_pending(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "team.manager.fee@example.com", "Team Manager")
    headers = _login(client, "team.manager.fee@example.com")
    _, division, _ = season_division_teams

    res = _submit(client, headers, division.id)

    assert res.status_code == 201
    body = res.json()
    assert float(body["registration_fee"]) == 1.0
    assert body["payment_status"] == "Pending"


def test_admin_can_mark_payment_paid_and_pending(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.pay@example.com", "League Administrator")
    headers = _login(client, "admin.pay@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id).json()["id"]

    paid = client.patch(
        f"/api/v1/registrations/{reg_id}/payment",
        json={"payment_status": "Paid"}, headers=headers,
    )
    assert paid.status_code == 200
    assert paid.json()["payment_status"] == "Paid"

    back = client.patch(
        f"/api/v1/registrations/{reg_id}/payment",
        json={"payment_status": "Pending"}, headers=headers,
    )
    assert back.status_code == 200
    assert back.json()["payment_status"] == "Pending"


def test_non_reviewer_cannot_mark_payment(client, dbsession, org, season_division_teams):
    submitter = _make_user(dbsession, org, "tm.pay@example.com", "Team Manager")
    _make_user(dbsession, org, "admin.pay2@example.com", "League Administrator")
    submit_headers = _login(client, "tm.pay@example.com")
    admin_headers = _login(client, "admin.pay2@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, submit_headers, division.id).json()["id"]

    res = client.patch(
        f"/api/v1/registrations/{reg_id}/payment",
        json={"payment_status": "Paid"}, headers=submit_headers,
    )
    assert res.status_code == 403

    # Sanity: the admin can still do it.
    assert client.patch(
        f"/api/v1/registrations/{reg_id}/payment",
        json={"payment_status": "Paid"}, headers=admin_headers,
    ).status_code == 200


def test_email_registrant_simulates_without_smtp(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.mail@example.com", "League Administrator")
    headers = _login(client, "admin.mail@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id).json()["id"]

    res = client.post(f"/api/v1/registrations/{reg_id}/email", headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["to"] == "nina@example.com"
    assert body["mode"] == "simulated"  # no SMTP configured in the test env


def test_email_requires_a_contact_email(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "admin.nomail@example.com", "League Administrator")
    headers = _login(client, "admin.nomail@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id, contact_email=None).json()["id"]

    res = client.post(f"/api/v1/registrations/{reg_id}/email", headers=headers)
    assert res.status_code == 400


def test_submitting_auto_emails_the_manager_account(caplog, client, dbsession, org, season_division_teams):
    caplog.set_level(logging.INFO, logger="sportsleague.email")
    _make_user(dbsession, org, "manager.ack@example.com", "Team Manager")
    headers = _login(client, "manager.ack@example.com")
    _, division, _ = season_division_teams

    # The typed contact_email differs from the manager's account email; the
    # auto-ack must go to the ACCOUNT email, not the typed one.
    res = _submit(client, headers, division.id, contact_email="someone.else@example.com")
    assert res.status_code == 201

    assert any("EMAIL SIMULATED" in r.message and "manager.ack@example.com" in r.message for r in caplog.records)
    assert any("wait for the administrator to approve" in r.message for r in caplog.records)
