"""
DB セッションを FastAPI の依存関係として提供するモジュール。

TypeScript の PrismaClient を `req` にぶら下げてハンドラで使うようなイメージで、
ここでは SQLAlchemy のセッションを `Depends` 経由で受け取ります。
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """DB セッションを生成・クリーンアップする依存関係。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
