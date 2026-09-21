import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

# Get Database Connection URL from .env (defaults to provided MySQL configuration)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+aiomysql://root:123456@localhost:3306/WebAPI?charset=utf8mb4"
)

# Async engine configured for high-concurrency MySQL connections
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"),
    future=True,
    pool_pre_ping=True,      # Automatically reconnect if connection was dropped
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_size=10,            # Main pool connection count
    max_overflow=20          # Max extra connections during high traffic
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Declarative base for all domain entities
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency to provide an isolated async database session per request.
    Repositories handle their own explicit commits/rollbacks.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
