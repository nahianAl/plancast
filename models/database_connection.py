"""
Database connection management for PlanCast.

This module handles database connections, session management, and connection pooling
for both synchronous and asynchronous operations.
"""

import os
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager

from config.settings import db_settings

# Database URLs
DATABASE_URL = db_settings.database_url
ASYNC_DATABASE_URL = db_settings.async_database_url

# Engine configuration for sync operations
SYNC_ENGINE_CONFIG = {
    "poolclass": QueuePool,
    "pool_size": db_settings.POSTGRES_POOL_SIZE,
    "max_overflow": db_settings.POSTGRES_MAX_OVERFLOW,
    "pool_timeout": db_settings.POSTGRES_POOL_TIMEOUT,
    "pool_recycle": db_settings.POSTGRES_POOL_RECYCLE,
    "pool_pre_ping": True,  # Verify connections before use
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",  # SQL logging
}

# Engine configuration for async operations
ASYNC_ENGINE_CONFIG = {
    "poolclass": NullPool,  # Async engines use NullPool by default
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",  # SQL logging
}

# Create engines
engine = create_engine(DATABASE_URL, **SYNC_ENGINE_CONFIG)
async_engine = create_async_engine(ASYNC_DATABASE_URL, **ASYNC_ENGINE_CONFIG)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

def get_database_url() -> str:
    """Get the current database URL."""
    return DATABASE_URL

def get_async_database_url() -> str:
    """Get the current async database URL."""
    return ASYNC_DATABASE_URL

def test_connection() -> bool:
    """Test database connection."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

async def test_async_connection() -> bool:
    """Test async database connection."""
    try:
        async with async_engine.begin() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Async database connection test failed: {e}")
        return False

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def create_tables():
    """Create all database tables."""
    from models.database import Base
    Base.metadata.create_all(bind=engine)

async def create_tables_async():
    """Create all database tables asynchronously."""
    from models.database import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def drop_tables():
    """Drop all database tables (DANGEROUS - use with caution)."""
    from models.database import Base
    Base.metadata.drop_all(bind=engine)

async def drop_tables_async():
    """Drop all database tables asynchronously (DANGEROUS - use with caution)."""
    from models.database import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

def get_database_info() -> dict:
    """Get database connection information."""
    return {
        "host": db_settings.POSTGRES_HOST,
        "port": db_settings.POSTGRES_PORT,
        "database": db_settings.POSTGRES_DB,
        "user": db_settings.POSTGRES_USER,
        "pool_size": db_settings.POSTGRES_POOL_SIZE,
        "max_overflow": db_settings.POSTGRES_MAX_OVERFLOW,
        "ssl_mode": db_settings.POSTGRES_SSL_MODE,
        "connection_test": test_connection(),
    }

# Database health check
def check_database_health() -> dict:
    """Check database health and return status."""
    try:
        # Test basic connection
        connection_ok = test_connection()
        
        # Test basic query
        query_ok = False
        if connection_ok:
            with get_db_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
                query_ok = result.scalar() is not None
        
        return {
            "status": "healthy" if connection_ok and query_ok else "unhealthy",
            "connection": "ok" if connection_ok else "failed",
            "query": "ok" if query_ok else "failed",
            "database_url": DATABASE_URL.replace(db_settings.POSTGRES_PASSWORD, "***") if connection_ok else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "connection": "failed",
            "query": "failed",
        }
