from collections.abc import AsyncGenerator

from redis import asyncio as aioredis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


async_engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
_redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_redis() -> aioredis.Redis:
    return _redis_client
