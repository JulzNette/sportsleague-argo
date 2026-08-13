"""
Global exception handlers that turn raw framework errors into messages an
end user can actually understand.

Without this, FastAPI's default 422 validation response is an array of
machine-readable objects like:
    [{"type":"string_too_short","loc":["body","name"],"msg":"String should
      have at least 1 character","input":""}]
which a non-technical user can't make sense of. Instead we flatten each
error into a sentence naming the exact field and what went wrong.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Field name (as it appears in the request body) -> friendly display label.
# Shared across all forms, so a generic label covers every entity.
_FIELD_LABELS = {
    "name": "Name",
    "full_name": "Full name",
    "coach_name": "Coach name",
    "contact_email": "Contact email",
    "contact_phone": "Contact phone",
    "email": "Email",
    "password": "Password",
    "team_id": "Team",
    "division_id": "Division",
    "season_id": "Season",
    "league_id": "League",
    "referee_id": "Referee",
    "home_team_id": "Home team",
    "away_team_id": "Away team",
    "license_number": "License number",
    "jersey_number": "Jersey number",
    "date_of_birth": "Date of birth",
    "position": "Position",
    "sport_type": "Sport type",
    "description": "Description",
    "scheduled_date": "Scheduled date",
    "scheduled_time": "Scheduled time",
    "venue": "Venue",
    "round_number": "Round number",
    "match_type": "Match type",
    "status": "Status",
    "start_date": "Start date",
    "end_date": "End date",
    "format": "Format",
    "max_teams": "Max teams",
    "home_score": "Home score",
    "away_score": "Away score",
    "result_type": "Result type",
    "forfeit_winner_team_id": "Forfeit winner team",
    "notes": "Notes",
    "type": "Type",
}


def _label(field: str) -> str:
    return _FIELD_LABELS.get(field, field.replace("_", " ").strip().title() or field)


def _field_name(loc) -> str:
    """Pull the last meaningful segment out of a pydantic error location."""
    for part in reversed(loc):
        if isinstance(part, str) and part not in ("body",):
            return part
    return "value"


def _humanize(error: dict) -> str:
    field = _field_name(error.get("loc", []))
    label = _label(field)
    error_type = error.get("type", "")
    ctx = error.get("ctx") or {}

    if error_type == "missing":
        return f"{label} is required."
    if error_type == "string_too_short":
        minimum = ctx.get("min_length")
        if minimum and minimum > 1:
            return f"{label} must be at least {minimum} characters."
        return f"{label} is required."
    if error_type == "string_too_long":
        return f"{label} must be at most {ctx.get('max_length')} characters."
    if error_type == "string_type":
        return f"{label} must be text."
    if error_type in ("int_type", "number_type"):
        return f"{label} must be a number."
    if error_type in ("uuid_type", "uuid_parsing"):
        return f"{label} must be a valid selection."
    if error_type == "date_type":
        return f"{label} must be a valid date."
    if error_type in ("email_type", "value_error") and "email" in str(error.get("msg", "")).lower():
        return f"{label} must be a valid email address."
    if error_type == "string_pattern_mismatch":
        return f"{label} has an invalid value."
    if error_type == "json_invalid":
        return "The request body is not valid JSON."
    if error_type == "bool_type":
        return f"{label} must be yes or no."
    # Fallback: use FastAPI's own human text when available.
    msg = error.get("msg") or "invalid value"
    if msg and msg.startswith("Value error"):
        msg = msg[len("Value error"):].strip()
    return f"{label}: {msg}."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        messages = [_humanize(err) for err in errors]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": messages if len(messages) > 1 else messages[0]},
        )
