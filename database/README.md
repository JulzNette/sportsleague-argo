# Database — PostgreSQL 14

This module's schema has **one source of truth**: the Alembic migration at
`backend/alembic/versions/0001_initial_schema.py`. `schema.sql` in this
folder is a plain-SQL mirror of that same migration, provided as a second,
Python-free way to stand the database up (e.g. if you just want to inspect
it in a GUI client, or apply it with `psql` directly). If the two ever
disagree, the Alembic migration wins — regenerate `schema.sql` to match it,
don't hand-edit them separately.

## Option A (recommended): let the backend manage it

This is what `docker compose up` at the project root does automatically.

```bash
cd backend
alembic upgrade head
python seed.py
```

## Option B: apply the raw SQL directly

```bash
createdb sportsleague_db
psql -d sportsleague_db -f schema.sql
```

Note: if you go this route, Alembic doesn't know the schema already exists.
Stamp it as up to date so future `alembic upgrade head` calls don't try to
recreate these tables:

```bash
cd ../backend && alembic stamp head
```

You'll still need to run `python seed.py` afterwards for demo data, since
`seed.py` inserts through SQLAlchemy (and needs Alembic to have run, or been
stamped, first).

## What's actually in it

11 tables: 2 local sandbox stubs (`organizations`, `users` — not part of the
module deliverable, see the comment at the top of `schema.sql`) and 9
`sportsleague_`-prefixed business tables. Full column-by-column contract
compliance notes are in the root `README.md`.

## Connecting

Default credentials (matching `backend/.env.example` and the root
`docker-compose.yml`):

```
Host:     localhost
Port:     5432
Database: sportsleague_db
User:     sportsleague_user
Password: sportsleague_pass
```
