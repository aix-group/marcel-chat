from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from marcel.config import DATABASE_URI
from marcel.models import Base


def get_database_uri():
    """Setup URI with dialect as per the installed drivers."""
    assert DATABASE_URI, "You must set a database URI."

    if "sqlite://" in DATABASE_URI:
        uri = DATABASE_URI
        uri_async = DATABASE_URI.replace("sqlite://", "sqlite+aiosqlite://")
    elif "mysql://" in DATABASE_URI:
        uri = DATABASE_URI.replace("mysql://", "mysql+pymysql://")
        uri_async = DATABASE_URI.replace("mysql://", "mysql+asyncmy://")
    else:
        raise ValueError("unsupported database")
    return uri, uri_async


uri, uri_async = get_database_uri()
engine = create_engine(
    uri, pool_pre_ping=True, pool_size=5, max_overflow=10, pool_recycle=1800
)
engine_async = create_async_engine(
    uri_async, pool_pre_ping=True, pool_size=5, max_overflow=10, pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine_async
)

# Make sure tables are created on app startup
Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_async():
    async with AsyncSessionLocal() as db:
        yield db
