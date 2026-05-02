"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

# Async engine — connects to PostgreSQL via asyncpg
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Session factory — use with `async with async_session() as session:`
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
