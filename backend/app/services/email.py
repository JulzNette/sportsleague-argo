"""
Email delivery for the Sports League module.

Real sending prefers the Brevo transactional HTTP API (port 443), which works
even on hosts whose network blocks raw SMTP/587 (e.g. Render's free tier).
When no Brevo key is configured it falls back to SMTP if available, otherwise
it SIMULATES the email by logging it so the feature never errors. Callers
always know whether a message was really delivered or only simulated.

Senders are branded as "ARGO" so outgoing mail is recognisable either way.
"""
import json
import logging
import smtplib
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import get_settings

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

logger = logging.getLogger("sportsleague.email")

SENDER_NAME = "ARGO"


def _amount(value) -> str:
    if value is None:
        return "Not set"
    try:
        return f"₱{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Not set"


def _simulate(from_name: str, subject: str, to: str, body: str) -> None:
    logger.info(
        "EMAIL SIMULATED (no SMTP configured)\nFrom: %s\nTo: %s\nSubject: %s\n\n%s",
        from_name, to, subject, body,
    )


def _deliver_via_brevo(subject: str, to: str, body: str) -> dict:
    """Send via Brevo's HTTPS API (works on hosts that block raw SMTP/587)."""
    settings = get_settings()
    sender = settings.BREVO_FROM_EMAIL or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    payload = {
        "sender": {"email": sender, "name": SENDER_NAME},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": body,
    }
    req = urllib.request.Request(
        BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
    except Exception as exc:  # noqa: BLE001 - surface failure to the caller
        logger.exception("Brevo send failed")
        return {"sent": False, "to": to, "mode": "brevo", "error": str(exc)}

    if 200 <= status < 300:
        return {"sent": True, "to": to, "mode": "brevo"}
    return {"sent": False, "to": to, "mode": "brevo", "error": f"HTTP {status}"}


def _deliver(subject: str, to: str, body: str) -> dict:
    """Send (or simulate) an email. Returns delivery metadata for callers."""
    settings = get_settings()
    if not to:
        _simulate(SENDER_NAME, subject, to, body)
        return {"sent": False, "to": to, "mode": "simulated"}

    # Preferred: Brevo HTTP API (port 443, works on Render free tier).
    if settings.BREVO_API_KEY:
        return _deliver_via_brevo(subject, to, body)

    # Fallback: raw SMTP.
    if settings.SMTP_HOST:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr((SENDER_NAME, settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME))
        msg["To"] = to
        msg.set_content(body)
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
        except Exception as exc:  # noqa: BLE001 - surface failure to the caller
            logger.exception("SMTP send failed; falling back to simulation")
            _simulate(SENDER_NAME, subject, to, body)
            return {"sent": False, "to": to, "mode": "simulated", "error": str(exc)}
        return {"sent": True, "to": to, "mode": "smtp"}

    _simulate(SENDER_NAME, subject, to, body)
    return {"sent": False, "to": to, "mode": "simulated"}


def send_verification_code_email(*, email: str, code: str) -> dict:
    """Email the 6-digit verification code needed to finish account creation."""
    subject = "Your verification code"
    body = (
        f"Hello,\n\n"
        f"Your verification code is:\n\n"
        f"    {code}\n\n"
        f"Enter this code to finish creating your account. It expires in 10 minutes.\n\n"
        f"If you didn't request this, you can safely ignore this email.\n\n"
        f"Thank you,\n{SENDER_NAME} Sports League"
    )
    return _deliver(subject, email, body)


def send_registration_ack_email(*, team_name: str, manager_email: str) -> dict:
    """Auto-sent to the manager right after they submit a registration."""
    subject = "Registration received — wait for approval"
    body = (
        f"Hello,\n\n"
        f"Thank you for registering your team '{team_name}'.\n\n"
        f"You have successfully registered. Your request is now pending review — "
        f"just wait for the administrator to approve your registration.\n\n"
        f"Thank you,\n{SENDER_NAME} Sports League"
    )
    return _deliver(subject, manager_email, body)


def send_registration_email(
    *,
    team_name: str,
    contact_email: str,
    registration_fee,
    payment_status: str,
    registration_status: str,
) -> dict:
    """Email the registrant (the address they typed) about their registration fee."""
    subject = f"Registration received: {team_name}"
    body = (
        f"Hello {team_name},\n\n"
        f"Your registration has been received.\n\n"
        f"  Registration status : {registration_status}\n"
        f"  Registration fee    : {_amount(registration_fee)}\n"
        f"  Payment status      : {payment_status}\n\n"
        f"Please complete your payment for the registration fee above to "
        f"finish securing your slot. If payment has already been made, no "
        f"further action is needed.\n\n"
        f"Thank you,\n{SENDER_NAME} Sports League"
    )
    return _deliver(subject, contact_email, body)
