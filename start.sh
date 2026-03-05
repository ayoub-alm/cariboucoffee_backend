#!/bin/bash
set -e

# Wait for DB
echo "Waiting for database connection..."
python << END
import asyncio
import os
import sys
import time
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_server = os.getenv("POSTGRES_SERVER", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "caribou")
    
    url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}"
    engine = create_async_engine(url)
    
    retries = 30
    while retries > 0:
        try:
            async with engine.connect() as conn:
                print(f"Database {db_server}:{db_port} is ready!")
            await engine.dispose()
            sys.exit(0)
        except Exception as e:
            print(f"Waiting for database at {db_server}:{db_port}...")
            time.sleep(2)
            retries -= 1
            
    print("Could not connect to database")
    sys.exit(1)

asyncio.run(check())
END

# Run migrations
echo "Running alembic migrations..."
alembic upgrade head

# Start server
echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
