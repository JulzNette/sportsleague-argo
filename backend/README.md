# Backend — Sports League Management API

Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL 14.

See the root `README.md` for the full three-part (database/backend/frontend)
picture and the one-command Docker setup. This file covers running the
backend on its own.

## Setup (manual, no Docker)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt --break-system-packages

cp .env.example .env              # edit if your DB credentials differ

alembic upgrade head              # creates all 11 tables
python seed.py                    # one org, one user per role, sample data

uvicorn app.main:app --reload --port 8020
```

- API docs: http://localhost:8020/docs
- Health check: http://localhost:8020/health

`seed.py` prints a login (email) per role — password for all of them is
`Password123!`.

## Project layout

```
app/
├── main.py                # FastAPI app + router registration
├── core/
│   ├── config.py          # settings from .env
│   ├── security.py        # password hashing + JWT
│   ├── permissions.py     # RBAC matrix (ported from the HTML prototype)
│   ├── state_machines.py  # status transition rules (seasons, matches)
│   └── deps.py            # auth + tenant-scoping dependencies
├── db/
│   ├── base.py             # Declarative base + OrgAuditMixin
│   └── session.py
├── models/                # SQLAlchemy models, 1 file per entity
├── schemas/                # Pydantic request/response models
├── services/
│   ├── crud.py             # generic tenant-scoped CRUD helpers
│   └── standings.py         # standings computed live, never stored
└── routers/                 # 1 router per entity + auth
```

## Key endpoints (all under `/api/v1`)

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login` |
| Leagues | `GET/POST /leagues`, `GET/PATCH/DELETE /leagues/{id}` |
| Seasons | `GET/POST /seasons`, `GET/PATCH /seasons/{id}` |
| Divisions | `GET/POST /divisions`, `GET/PATCH/DELETE /divisions/{id}` |
| Teams | `GET/POST /teams`, `GET/PATCH/DELETE /teams/{id}` |
| Players | `GET/POST /players`, `GET/PATCH/DELETE /players/{id}` |
| Referees | `GET/POST /referees`, `GET/PATCH /referees/{id}` |
| Matches | `GET/POST /matches`, `PATCH /matches/{id}`, `POST /matches/{id}/assign-referee`, `POST /matches/{id}/status` |
| Results | `GET/POST/PATCH /matches/{id}/result` |
| Standings | `GET /standings?season_id=...&division_id=...` |
| Reports | `GET/POST /reports`, `GET /reports/{id}/standings` |

## Migrations going forward

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Autogenerate works because `alembic/env.py` imports `app.models`, which
registers every table on the shared metadata.

## Docker

`Dockerfile` + `docker-entrypoint.sh` wait for Postgres, run migrations,
seed on first boot only, then serve. Driven by the root `docker-compose.yml`
— you normally won't build this image directly.
