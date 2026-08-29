"""
FastAPI application entrypoint for the Sports League Management module.
Run locally with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.rate_limit import limiter
from app.routers import (
    auth, coaches, divisions, leagues, matches, match_stats, notifications, players, referees,
    registrations, reports, results, scoring, seasons, standings, stats, superadmin, teams, users,
)
# `settings_router` alias avoids a name clash with the module-level `settings`
# object returned by get_settings() below.
from app.routers import settings as settings_router

settings = get_settings()

# Interactive docs are only for local development (database on localhost).
# They expose every route and schema, so they are turned off once the API is
# pointed at a real (remote) database.
show_docs = settings.ENVIRONMENT == "local" and "localhost" in settings.DATABASE_URL

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Sports League Management module (Argo Platform internship). "
        "Manages leagues, seasons, divisions, teams, players, referees, "
        "match scheduling, results, and computed standings."
    ),
    version="1.0.0",
    docs_url="/docs" if show_docs else None,
    redoc_url="/redoc" if show_docs else None,
    openapi_url="/openapi.json" if show_docs else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api)
app.include_router(leagues.router, prefix=api)
app.include_router(seasons.router, prefix=api)
app.include_router(divisions.router, prefix=api)
app.include_router(teams.router, prefix=api)
app.include_router(players.router, prefix=api)
app.include_router(coaches.router, prefix=api)
app.include_router(registrations.router, prefix=api)
app.include_router(notifications.router, prefix=api)
app.include_router(referees.router, prefix=api)
app.include_router(matches.router, prefix=api)
app.include_router(results.router, prefix=api)
app.include_router(scoring.router, prefix=api)
app.include_router(match_stats.router, prefix=api)
app.include_router(standings.router, prefix=api)
app.include_router(stats.router, prefix=api)
app.include_router(reports.router, prefix=api)
app.include_router(settings_router.router, prefix=api)
app.include_router(superadmin.router, prefix=api)
app.include_router(users.router, prefix=api)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
