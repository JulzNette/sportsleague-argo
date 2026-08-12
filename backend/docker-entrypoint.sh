#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import sys
from sqlalchemy import create_engine
from app.core.config import get_settings
try:
    create_engine(get_settings().DATABASE_URL).connect().close()
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is up."

echo "Applying migrations..."
alembic upgrade head

# Seed only on first run (organizations table empty)
SHOULD_SEED=$(python -c "
from sqlalchemy import create_engine, text
from app.core.config import get_settings
engine = create_engine(get_settings().DATABASE_URL)
with engine.connect() as conn:
    count = conn.execute(text('SELECT COUNT(*) FROM organizations')).scalar()
    print('yes' if count == 0 else 'no')
")
if [ "$SHOULD_SEED" = "yes" ]; then
  echo "Seeding demo data..."
  python seed.py
else
  echo "Demo data already present, skipping seed."
fi

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
