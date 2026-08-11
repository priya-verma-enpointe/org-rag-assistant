import asyncio
from sqlalchemy import text
from app.database import engine, Base
# Import models so they are registered on Base.metadata
from app.models import Organization, Document, DocumentChunk, ChatHistory

async def init_db():
    async with engine.begin() as conn:
        print("Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
