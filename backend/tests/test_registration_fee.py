"""
Registration fee + payment with the FLAT ADMIN-CONFIGURED fee model:
the amount is a single registration fee set by an Administrator, applied to
every division (per-division overrides are ignored). It is stored on the
registration, an admin can mark it Paid, and an admin can email the registrant
(simulated in tests).
"""
import logging

import pytest

from app.core.security import hash_password
from app.models.setting import AppSetting
from app.models.stub import User

PAYLOAD = {
    "team_name": "Silver Sharks",
    "coach_name": "Nina Ramos",
    "contact_email": "nina@example.com",
    "contact_phone": "09171234567",
    "registration_fee": 1.0,  # ignored now - the configured amount wins
    "notes": "Shared by the whole team.",
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


def _set_default_fee(dbsession, org, amount):
    row = dbsession.query(AppSetting).filter(
        AppSetting.organization_id == org.id, AppSetting.key == "registration_fee",
    ).first()
    if row is None:
        dbsession.add(AppSetting(
            organization_id=org.id, created_by=org.id, updated_by=org.id,
            key="registration_fee", value={"amount": float(amount)},
        ))
    else:
        row.value = {"amount": float(amount)}
    dbsession.commit()


def _set_division_fee(dbsession, org, division_id, amount):
    from app.models.setting import DivisionFee
    dbsession.add(DivisionFee(
        organization_id=org.id, created_by=org.id, updated_by=org.id,
        division_id=division_id, registration_fee=float(amount),
    ))
    dbsession.commit()


def test_submission_uses_admin_configured_fee_not_typed_amount(client, dbsession, org, season_division_teams):
    _set_default_fee(dbsession, org, 250)
    _make_user(dbsession, org, "team.manager.fee@example.com", "Team Manager")
    headers = _login(client, "team.manager.fee@example.com")
    _, division, _ = season_division_teams

    res = _submit(client, headers, division.id)

    assert res.status_code == 201
    body = res.json()
    assert float(body["registration_fee"]) == 250.0  # configured amount, not typed 1.0
    assert body["payment_status"] == "Pending"


@pytest.mark.no_default_fee
def test_submission_without_configured_fee_is_rejected(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "team.manager.nofee@example.com", "Team Manager")
    headers = _login(client, "team.manager.nofee@example.com")
    _, division, _ = season_division_teams

    res = _submit(client, headers, division.id)

    assert res.status_code == 400
    assert "registration fee" in res.json()["detail"].lower()


def test_division_fee_override_ignored_flat_fee_wins(client, dbsession, org, season_division_teams):
    # The league uses a single flat registration fee; a stored division override
    # must NOT change what a registrant pays.
    _set_default_fee(dbsession, org, 100)
    _, division, _ = season_division_teams
    _set_division_fee(dbsession, org, division.id, 350)

    _make_user(dbsession, org, "team.manager.ovr@example.com", "Team Manager")
    headers = _login(client, "team.manager.ovr@example.com")

    res = _submit(client, headers, division.id)
    assert res.status_code == 201
    assert float(res.json()["registration_fee"]) == 100.0


def test_admin_can_mark_payment_paid_and_pending(client, dbsession, org, season_division_teams):
    _set_default_fee(dbsession, org, 100)
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
    _set_default_fee(dbsession, org, 100)
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

    assert client.patch(
        f"/api/v1/registrations/{reg_id}/payment",
        json={"payment_status": "Paid"}, headers=admin_headers,
    ).status_code == 200


def test_email_registrant_simulates_without_smtp(client, dbsession, org, season_division_teams):
    _set_default_fee(dbsession, org, 100)
    _make_user(dbsession, org, "admin.mail@example.com", "League Administrator")
    headers = _login(client, "admin.mail@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id).json()["id"]

    res = client.post(f"/api/v1/registrations/{reg_id}/email", headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["to"] == "nina@example.com"
    assert body["mode"] == "simulated"


def test_email_requires_a_contact_email(client, dbsession, org, season_division_teams):
    _set_default_fee(dbsession, org, 100)
    _make_user(dbsession, org, "admin.nomail@example.com", "League Administrator")
    headers = _login(client, "admin.nomail@example.com")
    _, division, _ = season_division_teams
    reg_id = _submit(client, headers, division.id, contact_email=None).json()["id"]

    res = client.post(f"/api/v1/registrations/{reg_id}/email", headers=headers)
    assert res.status_code == 400


def test_submitting_auto_emails_the_manager_account(caplog, client, dbsession, org, season_division_teams):
    caplog.set_level(logging.INFO, logger="sportsleague.email")
    _set_default_fee(dbsession, org, 100)
    _make_user(dbsession, org, "manager.ack@example.com", "Team Manager")
    headers = _login(client, "manager.ack@example.com")
    _, division, _ = season_division_teams

    res = _submit(client, headers, division.id, contact_email="someone.else@example.com")
    assert res.status_code == 201

    assert any("EMAIL SIMULATED" in r.message and "manager.ack@example.com" in r.message for r in caplog.records)
    assert any("wait for the administrator to approve" in r.message for r in caplog.records)


# ---- Settings endpoints (admin fee config + public pricing/rewards) ----
def _admin_headers(client, dbsession, org, email="sysadmin.settings@example.com"):
    _make_user(dbsession, org, email, "System Administrator")
    return _login(client, email)


def test_public_settings_exposes_fee(client, dbsession, org, season_division_teams):
    _set_default_fee(dbsession, org, 500)
    res = client.get("/api/v1/settings/public")
    assert res.status_code == 200
    assert float(res.json()["registration_fee"]) == 500.0


def test_admin_can_set_default_fee_and_division_fee(client, dbsession, org, season_division_teams):
    headers = _admin_headers(client, dbsession, org)
    _, division, _ = season_division_teams

    put = client.put("/api/v1/settings/fee", json={"amount": 400}, headers=headers)
    assert put.status_code == 200
    assert float(put.json()["amount"]) == 400.0

    d = client.get("/api/v1/settings", headers=headers)
    assert d.status_code == 200
    assert float(d.json()["registration_fee"]) == 400.0
    assert d.json()["configured_fee"] is True

    df = client.put(
        "/api/v1/settings/division-fees",
        json={"division_id": str(division.id), "registration_fee": 600}, headers=headers,
    )
    assert df.status_code == 200
    assert float(df.json()["registration_fee"]) == 600.0

    d2 = client.get("/api/v1/settings", headers=headers)
    assert len(d2.json()["division_fees"]) == 1


def test_team_manager_cannot_access_admin_settings(client, dbsession, org, season_division_teams):
    _make_user(dbsession, org, "tm.block@example.com", "Team Manager")
    headers = _login(client, "tm.block@example.com")
    res = client.get("/api/v1/settings", headers=headers)
    assert res.status_code == 403


def test_admin_can_set_pricing_and_rewards_content(client, dbsession, org, season_division_teams):
    headers = _admin_headers(client, dbsession, org)
    _set_default_fee(dbsession, org, 500)

    pricing = [
        {"title": "Team registration", "amount": 500, "description": "Covers court time, refs, and scoreboards."},
    ]
    rewards = [{"division": "Open Men's", "place": "Champion", "prize": "Trophy + ₱5,000"}]

    pr = client.put("/api/v1/settings/content", json={"key": "pricing_content", "items": pricing}, headers=headers)
    assert pr.status_code == 200
    rw = client.put("/api/v1/settings/content", json={"key": "rewards_content", "items": rewards}, headers=headers)
    assert rw.status_code == 200

    pub = client.get("/api/v1/settings/public").json()
    assert pub["pricing"][0]["title"] == "Team registration"
    assert pub["rewards"][0]["division"] == "Open Men's"


def test_public_rewards_show_default_podium_when_unconfigured(client, dbsession, org):
    pub = client.get("/api/v1/settings/public").json()
    places = [r["place"] for r in pub["rewards"]]
    assert "Champion" in places
    assert "1st" in places
    assert "2nd" in places


def test_public_division_fee_resolver(client, dbsession, org, season_division_teams):
    _set_default_fee(dbsession, org, 100)
    _, division, _ = season_division_teams
    res = client.get(f"/api/v1/settings/public/divisions/{division.id}/fee")
    assert res.status_code == 200
    assert float(res.json()["registration_fee"]) == 100.0


def test_public_division_fee_resolver_ignores_override(client, dbsession, org, season_division_teams):
    # With a flat fee model, the resolver returns the default fee even when a
    # division override row exists.
    _set_default_fee(dbsession, org, 100)
    _, division, _ = season_division_teams
    _set_division_fee(dbsession, org, division.id, 700)
    res = client.get(f"/api/v1/settings/public/divisions/{division.id}/fee")
    assert res.status_code == 200
    assert float(res.json()["registration_fee"]) == 100.0
