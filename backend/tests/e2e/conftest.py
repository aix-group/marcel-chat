from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from marcel.app import build_app
from marcel.database import get_database_uri, get_db, get_db_async
from marcel.models import Base

uri, uri_async = get_database_uri()

engine = create_engine(
    uri,
    connect_args={"check_same_thread": False} if "sqlite" in uri else {},
    pool_pre_ping=True,
)

async_engine = create_async_engine(
    uri_async,
    connect_args={"check_same_thread": False} if "sqlite" in uri else {},
    pool_pre_ping=True,
)


@pytest.fixture(scope="function")
def session_factory():
    connection = engine.connect()
    transaction = connection.begin()
    try:
        # Each session will share the same connection (and thus the same transaction)
        yield sessionmaker(autocommit=False, autoflush=False, bind=connection)
    finally:
        transaction.rollback()
        connection.close()


@pytest_asyncio.fixture(scope="function")
async def session_factory_async():
    connection = await async_engine.connect()
    transaction = await connection.begin()
    try:
        # Each session will share the same connection (and thus the same transaction)
        yield async_sessionmaker(autocommit=False, autoflush=False, bind=connection)
    finally:
        await transaction.rollback()
        await connection.close()
        # for AsyncEngine created in function scope, close and clean-up pooled connections
        # See: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
        await async_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(session_factory, session_factory_async):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield {"pipeline": None}

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    async def override_get_db_async():
        db = session_factory_async()
        try:
            yield db
        finally:
            await db.close()

    app = build_app(lifespan)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_async] = override_get_db_async

    with TestClient(app) as client:
        yield client
