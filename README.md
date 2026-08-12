# Sports League Management — Argo Platform Module

A complete, three-part rebuild of the original in-memory HTML/JS prototype
(`sports-league-management.html`) into a real application: **PostgreSQL 14
database → Python 3.11 / FastAPI backend → React 18 / Vite / Tailwind
frontend**, wired together end-to-end.

```
sportsleague-argo/
├── vercel.json             ← Vercel config (frontend/ subdir, SPA routing)
├── render.yaml             ← Render blueprint (backend/ web service)
├── docker-compose.yml      ← optional local one-command run
├── database/               ← PostgreSQL 14 schema (reference SQL + docs)
├── backend/                ← FastAPI + SQLAlchemy 2.0 + Alembic API (Render)
└── frontend/               ← React 18 + Vite + Tailwind UI (Vercel)
```

## Hosting stack (this repo's production setup)

| Piece | Hosted by | Notes |
|---|---|---|
| Code | GitHub | this repository |
| Frontend | Vercel | static React/Vite build, `frontend/` subdir |
| Backend | Render | FastAPI web service, `backend/` subdir |
| Database | Neon | free cloud PostgreSQL 14, already used by `DATABASE_URL` |

## Deploy in ~10 minutes

**1. GitHub** — `git init`, push this folder to a new repo (`.env` files are
gitignored so secrets never get committed).

**2. Render (backend)** — New → Blueprint → connect the GitHub repo. Pick
`render.yaml`. Render builds `backend/` and runs
`alembic upgrade head && uvicorn ...`. Then set these env vars in the Render
dashboard:
- `DATABASE_URL` — your Neon connection string
- `JWT_SECRET_KEY` — a long random string
- `CORS_ORIGINS` — e.g. `["https://sportsleague-frontend.vercel.app"]`

Your API URL will be like `https://sportsleague-api.onrender.com`.

**3. Vercel (frontend)** — Add New Project → import the same repo → Vercel
reads `vercel.json` (root directory `frontend/`). Set the environment
variable `VITE_API_BASE_URL` to your Render API URL, e.g.
`https://sportsleague-api.onrender.com/api/v1`, then deploy.

**4. Optional:** run `python seed.py` once against Neon (inside `backend/`)
to load the six demo logins, if the database is empty.

## Run locally (no Docker, no accounts)

**1. Database** — see `database/README.md`. Quickest path:
```sql
CREATE DATABASE sportsleague_db;
CREATE USER sportsleague_user WITH PASSWORD 'sportsleague_pass';
GRANT ALL PRIVILEGES ON DATABASE sportsleague_db TO sportsleague_user;
```

**2. Backend** — see `backend/README.md` for full detail:
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt --break-system-packages
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8020
```

**3. Frontend** — see `frontend/README.md`:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Then open http://localhost:5173 and log in with any seeded account (e.g.
`system.administrator@gmail.com` / `Password123!`) — the login page shows
all six demo logins as quick-pick buttons.

## Contract compliance (unchanged from the backend-only delivery)

| Contract rule | Implementation |
|---|---|
| UUID primary keys, no serial ints | Every table's `id` is `UUID`, `default=uuid.uuid4` |
| `organization_id` on every business table | FK → `organizations.id`, `ON DELETE CASCADE`, `NOT NULL`, indexed |
| Audit columns everywhere | `created_at/updated_at/created_by/updated_by`, loose UUIDs, no FK to `users` |
| `sportsleague_` table prefix | All 9 business tables |
| No FK to other modules' tables | Only `organizations.id` referenced outside this module |
| Unique constraints lead with `organization_id` | e.g. `uq_sportsleague_teams_org_division_name` |
| Never store derived/calculated values | Standings + report content computed live on every request — see `backend/app/services/standings.py` |

## What each layer does

- **`database/`** — PostgreSQL 14. `schema.sql` is a plain-SQL mirror of the
  Alembic migration for anyone who wants to inspect or apply the schema
  without touching Python. Alembic remains the source of truth.
- **`backend/`** — FastAPI. RBAC (`app/core/permissions.py`) and status
  state machines (`app/core/state_machines.py`) are enforced **server-side**
  — the frontend mirrors both purely for UI polish (disabling buttons a role
  can't use), never as the actual security boundary.
- **`frontend/`** — React + Vite + Tailwind + React Query + Zustand + axios,
  per your onboarding stack. Pages: Dashboard, Leagues, Seasons, Divisions,
  Teams, Players, Referees, Matches (scheduling, referee assignment, status
  transitions, result submission), Standings (always live), Reports.

## What's still a local-only stub

`organizations` and `users` (`backend/app/models/stub.py`,
`database/schema.sql`'s first two tables) are a throwaway sandbox stand-in
for tables the real Argo platform owns elsewhere — needed so this module can
run standalone, but not meant to be handed over as part of the deliverable.

## Trying the RBAC out

Log in as `player@gmail.com` (password `Password123!`) and try to
schedule a match — the button won't even render, because the frontend
mirrors the permission matrix. Log in as `league.administrator@gmail.com`
and try the same action against a season that's already `Cancelled` — the
button renders, but the backend rejects it with a 400 explaining the status
transition isn't allowed. Both layers are doing real work, but only the
backend one is load-bearing.
