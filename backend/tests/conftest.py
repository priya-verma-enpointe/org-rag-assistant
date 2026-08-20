import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    HTTPX AsyncClient fixture.
    Runs against the actual database session manager without overriding get_db.
    This guarantees that requests, background tasks, and generator streams
    each resolve their own independent sessions, preventing pgBouncer / asyncpg conflicts.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-API-Key": settings.API_KEY}) as ac:
        yield ac
