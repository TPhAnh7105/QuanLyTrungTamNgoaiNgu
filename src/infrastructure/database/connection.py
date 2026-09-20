from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

DATABASE_URL = "sqlite+aiosqlite:///./language_center.db"

# Create async engine for SQLite
# echo=True will log all SQL commands
engine = create_async_engine(
    DATABASE_URL, 
    echo=True, 
    future=True, 
    connect_args={"check_same_thread": False}
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Declarative base for models
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session for each request.
    Repositories are responsible for calling commit() themselves.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

