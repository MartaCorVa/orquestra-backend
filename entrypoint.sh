#!/bin/sh

echo "Waiting for database..."

until python -c "import os, psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])" >/dev/null 2>&1; do
  sleep 2
done

echo "Database is ready"

python -m app.init_db
python -m app.seed

uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}