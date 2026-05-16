#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start gunicorn in production mode
echo "Starting FastAPI server..."
exec gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --access-logfile -
