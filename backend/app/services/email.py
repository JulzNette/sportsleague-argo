"""
Email delivery for the Sports League module.

Real sending uses the SMTP settings from env (SMTP_HOST/USERNAME/etc.). When
those aren't configured - like during a class demo where the presenter just
wants to show the flow - the service SIMULATES the email by logging it, so the
feature works end-to-end without any credentials. Callers always know whether
a message was really delivered or only simulated.

Senders are branded as "ARGO" so outgoing mail is recognisable either way.
"""
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import get_settings

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


def _deliver(subject: str, to: str, body: str) -> dict:
    """Send (or simulate) an email. Returns delivery metadata for callers."""
    settings = get_settings()
    if not settings.SMTP_HOST or not to:
        _simulate(SENDER_NAME, subject, to, body)
        return {"sent": False, "to": to, "mode": "simulated"}

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
