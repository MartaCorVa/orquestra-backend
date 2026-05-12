#!/bin/sh

echo "Starting application..."

python -m app.init_db
python -m app.seed

uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}