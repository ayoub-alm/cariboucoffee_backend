import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Override settings for local migration
# Docker exposes DB on 5440
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5440/caribou"

async def run_migration():
    print(f"Connecting to {DB_URL}...")
    engine = create_async_engine(DB_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Starting migration...")
        
        # Add correct_answer column
        try:
            await conn.execute(text("ALTER TABLE audit_questions ADD COLUMN correct_answer VARCHAR DEFAULT 'oui'"))
            print("Added correct_answer to audit_questions")
        except Exception as e:
            print(f"Adding correct_answer failed (likely exists): {e}")

        # Add na_score column
        try:
            await conn.execute(text("ALTER TABLE audit_questions ADD COLUMN na_score INTEGER DEFAULT 0"))
            print("Added na_score to audit_questions")
        except Exception as e:
            print(f"Adding na_score failed (likely exists): {e}")

        # Add choice column to audit_answers
        try:
            await conn.execute(text("ALTER TABLE audit_answers ADD COLUMN choice VARCHAR"))
            print("Added choice to audit_answers")
        except Exception as e:
            print(f"Adding choice failed (likely exists): {e}")
            
        print("Migration complete.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
