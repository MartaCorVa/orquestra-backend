#!/bin/sh

echo "Waiting for database..."

while ! python -c "import psycopg2; psycopg2.connect(host='db', dbname='orquestra_db', user='postgres', password='postgres')" >/dev/null 2>&1; do
  sleep 2
done

echo "Database is ready"

python -m app.seed

uvicorn main:app --host 0.0.0.0 --port 8000