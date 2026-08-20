import asyncio
import sys
import os

# Add parent directory to path so app modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import engine

async def migrate():
    async with engine.begin() as conn:
        print("Running column migrations...")
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'COMPLETED';"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT;"))
        print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
