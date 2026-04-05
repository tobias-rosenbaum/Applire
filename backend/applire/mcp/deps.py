"""
DB session dependency for the MCP server.

The FastAPI DI system is not available here, so we expose a plain async
context manager that wraps AsyncSessionLocal directly.  Each tool handler
opens a short-lived session and closes it after the service call completes.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from applire.db.session import AsyncSessionLocal


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
