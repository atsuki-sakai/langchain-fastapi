"""
SQLAlchemy のユーザースキーマ（DB モデル）。

TypeScript の ORM（Prisma/TypeORM/Sequelize）でのモデル定義に相当します。
`app.models.user` の Pydantic モデルとは役割が異なり、こちらはテーブル定義です。
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """ユーザーの SQLAlchemy モデル（テーブル定義）。"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"