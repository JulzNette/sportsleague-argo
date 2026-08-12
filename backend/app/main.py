"""
FastAPI application entrypoint for the Sports League Management module.
Run locally with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    auth, divisions, leagues, matches, players, referees,
    reports, results, seasons, standings, teams,
)

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Sports League Management module (Argo Platform internship). "
        "Manages leagues, seasons, divisions, teams, players, referees, "
        "match scheduling, results, and computed standings."
    ),
    version="1.0.0",
)

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
app.include_router(referees.router, prefix=api)
app.include_router(matches.router, prefix=api)
app.include_router(results.router, prefix=api)
app.include_router(standings.router, prefix=api)
app.include_router(reports.router, prefix=api)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
