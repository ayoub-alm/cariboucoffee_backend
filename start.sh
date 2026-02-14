#!/bin/bash
set -e

# Wait for DB? (Can add wait-for-it script later if needed, but 'depends_on' helps)

# Run migrations
echo "Running alembic migrations..."
alembic upgrade head

# Start server
echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
