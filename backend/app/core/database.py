"""
LEARN: Database connection and sessions
========================================
Like your Prisma client: one place that creates the engine and sessions.
We use async SQLAlchemy with asyncpg for non-blocking DB access.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Sync URL for Alembic; async for app (replace scheme for asyncpg)
DATABASE_URL_ASYNC = (
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    if settings.DATABASE_URL.startswith("postgresql://")
    else settings.DATABASE_URL
)

engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=settings.APP_ENV == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency: yield a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
