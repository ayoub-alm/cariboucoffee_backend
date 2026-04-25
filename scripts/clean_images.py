import asyncio
import json
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Database configuration from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "caribou")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Upload directory in the container
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/app/static/uploads")

async def get_used_photos():
    engine = create_async_engine(DATABASE_URL)
    used_files = set()

    try:
        async with engine.connect() as conn:
            # Get photos from audit_answers
            result = await conn.execute(text("SELECT photo_url FROM audit_answers WHERE photo_url IS NOT NULL"))
            for row in result:
                val = row[0]
                if not val:
                    continue
                try:
                    urls = json.loads(val)
                    if isinstance(urls, list):
                        for u in urls:
                            if isinstance(u, str):
                                used_files.add(os.path.basename(u))
                    elif isinstance(urls, str):
                        used_files.add(os.path.basename(urls))
                except json.JSONDecodeError:
                    # Fallback for legacy single-string paths
                    used_files.add(os.path.basename(val))

            # Get photos from audits
            result = await conn.execute(text("SELECT photo_url FROM audits WHERE photo_url IS NOT NULL"))
            for row in result:
                val = row[0]
                if not val:
                    continue
                try:
                    urls = json.loads(val)
                    if isinstance(urls, list):
                        for u in urls:
                            if isinstance(u, str):
                                used_files.add(os.path.basename(u))
                    elif isinstance(urls, str):
                        used_files.add(os.path.basename(urls))
                except json.JSONDecodeError:
                    used_files.add(os.path.basename(val))

    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

    return used_files

async def clean_uploads():
    print(f"--- Starting Image Cleanup ---")
    print(f"Checking directory: {UPLOAD_DIR}")
    
    if not os.path.exists(UPLOAD_DIR):
        print(f"Error: Directory {UPLOAD_DIR} does not exist.")
        return

    used_photos = await get_used_photos()
    print(f"Found {len(used_photos)} unique used images in database.")

    all_files = os.listdir(UPLOAD_DIR)
    deleted_count = 0
    total_size = 0

    for filename in all_files:
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue

        if filename not in used_photos:
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted_count += 1
                total_size += file_size
                print(f"Deleted unused image: {filename} ({file_size / 1024:.2f} KB)")
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")

    print(f"--- Cleanup Complete ---")
    print(f"Deleted {deleted_count} unused images.")
    print(f"Freed up {total_size / (1024 * 1024):.2f} MB.")

if __name__ == "__main__":
    asyncio.run(clean_uploads())
