"""
Email delivery for the Sports League module.

Real sending uses the SMTP settings from env (SMTP_HOST/USERNAME/etc.). When
those aren't configured - like during a class demo where the presenter just
wants to show the flow - the service SIMULATES the email by logging it, so the
feature works end-to-end without any credentials. The sender can always see
whether a message was really delivered or only simulated.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("sportsleague.email")


def _amount(value) -> str:
    if value is None:
        return "Not set"
    try:
        return f"₱{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Not set"


def _simulate(subject: str, to: str, body: str) -> None:
    logger.info(
        "EMAIL SIMULATED (no SMTP configured)\nTo: %s\nSubject: %s\n\n%s",
        to, subject, body,
    )


def send_registration_email(
    *,
    team_name: str,
    contact_email: str,
    registration_fee,
    payment_status: str,
    registration_status: str,
) -> dict:
    """Email the registrant (the address they typed) about their registration.

    Returns metadata about the delivery so callers can show whether it was
    really emailed or just simulated for the demo.
    """
    settings = get_settings()
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
        f"Thank you,\nSports League Management"
    )

    if not settings.SMTP_HOST or not contact_email:
        _simulate(subject, contact_email, body)
        return {"sent": False, "to": contact_email, "mode": "simulated"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    msg["To"] = contact_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as exc:  # noqa: BLE001 - surface failure to the caller
        logger.exception("SMTP send failed; falling back to simulation")
        _simulate(subject, contact_email, body)
        return {"sent": False, "to": contact_email, "mode": "simulated", "error": str(exc)}

    return {"sent": True, "to": contact_email, "mode": "smtp"}
