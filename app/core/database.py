"""
データベース接続管理。

- 同期エンジン: マイグレーションやテスト向け（SQLAlchemy ORM セッション）
- 非同期エンジン: アプリ実行時の非同期処理向け（AsyncSession）

TypeScript の `knex` + `pg` での Pool と同様の役割を担い、
依存関係としてセッションを供給するユーティリティも提供します。
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

settings = get_settings()

# Synchronous database setup (for migrations and simple operations)
engine = None
SessionLocal = None

if settings.database_url:
    # Convert async URL to sync for synchronous operations
    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous database setup
async_engine = None
AsyncSessionLocal = None

if settings.database_url:
    async_engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.is_development,  # Log SQL queries in development
    )
    AsyncSessionLocal = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
    )

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """非同期 DB セッションを提供する依存関係。"""
    if not AsyncSessionLocal:
        raise RuntimeError("Database not configured")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db():
    """同期 DB セッションを提供する依存関係。"""
    if not SessionLocal:
        raise RuntimeError("Database not configured")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db() -> None:
    """DB テーブルを初期化（マイグレーション相当の簡易処理）。"""
    if not async_engine:
        raise RuntimeError("Async database engine not configured")

    # Import all models here to ensure they are registered with SQLAlchemy
    from app.schemas import user  # noqa

    async with async_engine.begin() as conn:
        # Drop all tables (use with caution!)
        # await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """DB 接続をクローズし、プールを開放。"""
    if async_engine:
        await async_engine.dispose()
