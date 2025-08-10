"""
アプリケーション設定の読み込みとバリデーション。

環境変数/.env を Pydantic Settings で読み込み、型安全に扱います。
TypeScript の `zod` + `dotenv` 構成に近く、検証エラーで起動時に失敗します。
環境(`ENVIRONMENT`)に応じて `.env.dev` などを自動選択します。
"""

from typing import Optional, List
import os
from functools import lru_cache

# Pydantic v2 対応インポート
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリ設定（環境変数と.envから読み込み）。

    validation_alias を指定することで、ENV 名と属性名の乖離を吸収しています。
    """

    # Pydantic Settings の基本設定（デフォルトは .env）
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="FastAPI Application", validation_alias="APP_NAME")
    version: str = Field(default="1.0.0", validation_alias="VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # API Settings
    api_prefix: str = Field(default="/api/v1", validation_alias="API_PREFIX")
    # Note: pydantic-settings は List[str] を環境変数から読み込む際に JSON を要求するため
    # カンマ区切りの入力を許容したい場合は一旦 str として受け取り、プロパティで配列に変換する
    cors_origins_env: Optional[str] = Field(default=None, validation_alias="CORS_ORIGINS")

    # Database
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    database_test_url: Optional[str] = Field(default=None, validation_alias="DATABASE_TEST_URL")

    # Security
    secret_key: str = Field(validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")

    # Password hashing
    bcrypt_rounds: int = Field(default=12, validation_alias="BCRYPT_ROUNDS")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default="json", validation_alias="LOG_FORMAT")

    # Rate limiting
    rate_limit_requests: int = Field(default=100, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_per_minutes: int = Field(default=1, validation_alias="RATE_LIMIT_PER_MINUTES")

    # CORS_ORIGINS の派生プロパティ（文字列→配列変換）
    @property
    def cors_origins(self) -> List[str]:
        if not self.cors_origins_env:
            return []
        return [i.strip() for i in self.cors_origins_env.split(",") if i.strip()]

    # セキュリティ: SECRET_KEY の必須・長さチェック
    @field_validator("secret_key", mode="before")
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY must be set")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    # 環境値のバリデーション
    @field_validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "testing", "staging", "production"]:
            raise ValueError("Invalid environment")
        return v

    # 補助プロパティ
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


def get_env_file() -> str:
    """現在の `ENVIRONMENT` に応じて読み込む .env ファイルを決定。"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "development":
        return ".env.dev"
    elif env == "testing":
        return ".env.test"
    elif env == "staging":
        return ".env.staging"
    else:  # production
        return ".env"


@lru_cache()
def get_settings() -> Settings:
    """Settings のインスタンスをキャッシュして返す（env_file は動的切替）。"""
    env_file = get_env_file()
    # インスタンス生成時に _env_file を指定して読み込む
    return Settings(_env_file=env_file)