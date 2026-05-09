"""Pytest fixtures for backend tests.

Integration tests run against a real Postgres test database.
Default URL targets the docker-compose `db` service on host port 5434
with a separate `app_test` database — override via env var
`TEST_DATABASE_URL` if your Postgres lives elsewhere.
"""

import os

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.deps import get_db
from src.main import app
from src.models.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/app_test",
)


def _admin_dsn_and_dbname(test_url: str) -> tuple[str, str]:
    """Return (asyncpg DSN to the `postgres` admin DB, target DB name)."""
    # postgresql+asyncpg://user:pass@host:port/dbname → postgresql://user:pass@host:port/postgres + 'dbname'
    no_driver = test_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    base, dbname = no_driver.rsplit("/", 1)
    return f"{base}/postgres", dbname


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def _ensure_test_db():
    """Create the test database if it doesn't already exist."""
    admin_dsn, dbname = _admin_dsn_and_dbname(TEST_DATABASE_URL)
    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname=$1", dbname
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        await conn.close()
    yield


@pytest_asyncio.fixture(scope="session")
async def test_engine(_ensure_test_db):
    """Session-scoped async engine; create_all on entry, drop_all on exit."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Per-test session bound to the test engine."""
    session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine):
    """httpx async client with `get_db` overridden onto the test engine."""
    session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)
