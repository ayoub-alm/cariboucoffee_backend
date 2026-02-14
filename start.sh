#!/bin/bash
set -e

# Wait for DB
echo "Waiting for database connection..."
python << END
import socket
import time
import os
import sys

host = os.getenv('POSTGRES_SERVER', 'db')
port = int(os.getenv('POSTGRES_PORT', 5432))
retries = 30

while retries > 0:
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f'Database {host}:{port} is reachable')
            sys.exit(0)
    except OSError:
        print(f'Waiting for database at {host}:{port}...')
        time.sleep(2)
        retries -= 1

print('Could not connect to database')
sys.exit(1)
END

# Run migrations
echo "Running alembic migrations..."
alembic upgrade head

# Start server
echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
