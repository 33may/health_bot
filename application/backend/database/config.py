import os
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://may:may@localhost/storage")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

@asynccontextmanager
async def open_async_connection() -> AsyncGenerator[Any, Any]:
    """
    Async context manager that yields an AsyncSession.
    Usage:
        async with open_async_connection() as session:
            # use session for database operations
    """
    async with async_session() as session:
        yield session
