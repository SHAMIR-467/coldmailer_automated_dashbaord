from collections.abc import AsyncGenerator
from functools import lru_cache
import asyncio
from pathlib import Path

from fastapi import HTTPException
from redis import asyncio as aioredis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_schema_lock = asyncio.Lock()
_schema_ready = False


def _database_url() -> str:
    return settings.database_url


def _ensure_sqlite_parent(url: str) -> None:
    if url.startswith("sqlite"):
        # sqlite:///F:/path/to/file.db -> F:/path/to/file.db
        path = url.split("///", 1)[-1]
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _engine_kwargs(url: str) -> dict[str, object]:
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


@lru_cache
def get_async_engine():
    url = _database_url()
    _ensure_sqlite_parent(url)
    return create_async_engine(url, **_engine_kwargs(url))


@lru_cache
def get_sync_engine():
    url = settings.sync_database_url
    _ensure_sqlite_parent(url)
    return create_engine(url, **_engine_kwargs(url))


@lru_cache
def get_async_sessionmaker():
    return async_sessionmaker(get_async_engine(), expire_on_commit=False, class_=AsyncSession)


@lru_cache
def get_sync_sessionmaker():
    return sessionmaker(bind=get_sync_engine(), expire_on_commit=False)


class _AsyncSessionFactory:
    def __call__(self) -> AsyncSession:
        return get_async_sessionmaker()()


class _SyncSessionFactory:
    def __call__(self):
        return get_sync_sessionmaker()()


AsyncSessionLocal = _AsyncSessionFactory()
SessionLocal = _SyncSessionFactory()


@lru_cache
def get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


def reset_database_resources() -> None:
    global _schema_ready
    get_async_engine.cache_clear()
    get_sync_engine.cache_clear()
    get_async_sessionmaker.cache_clear()
    get_sync_sessionmaker.cache_clear()
    get_redis.cache_clear()
    _schema_ready = False


async def ensure_database_schema() -> None:
    global _schema_ready
    if _schema_ready:
        return
    async with _schema_lock:
        if _schema_ready:
            return
        async with get_async_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _schema_ready = True


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if not settings.database_url_or_none():
        raise HTTPException(status_code=503, detail="Database is not configured")
    await ensure_database_schema()
    async with AsyncSessionLocal() as session:
        yield session
