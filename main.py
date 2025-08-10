"""
アプリケーションのエントリーポイント。

このモジュールでは以下を行います:
- ロギングの初期化
- 設定(`Settings`)の読み込み
- FastAPI アプリケーションの生成とライフサイクル管理
- CORS や構造化ロギング等のミドルウェア追加
- 例外ハンドラの登録
- バージョン付き API ルーターの組み込み

TypeScript の Express などに近い概念として、FastAPI アプリは
"アプリケーション本体 + ルーター + 依存関係(Dependency)" で構成されます。
ここでは `lifespan` コンテキストマネージャで起動・終了時の処理を定義し、
DB 接続の初期化/クローズを行います。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.error_handlers import setup_error_handlers
from app.core.logging import LoggingMiddleware, configure_logging

# Configure logging first
configure_logging()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリのライフサイクルを管理するコンテキストマネージャ。

    - 起動時: DB が設定されていればテーブルを初期化
    - 終了時: DB リソースを破棄

    FastAPI では `lifespan` を使うことで、Express の `app.listen` 前後で
    何かを行うのと同様の初期化/後始末を避けられます。
    """
    # Startup フェーズ
    if settings.database_url:
        await init_db()
    # ここでアプリケーションの稼働期間に入る
    yield
    # Shutdown フェーズ
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Enterprise-grade FastAPI application with clean architecture",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    lifespan=lifespan,
)

# Setup error handlers
setup_error_handlers(app)

# CORS ミドルウェアの追加
# TypeScript の `cors` 中間処理と同様に、オリジン/メソッド/ヘッダの許可を設定します。
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# バージョン付き API ルーターの組み込み。
# `settings.api_prefix` (例: /api/v1) が全エンドポイントの先頭に付与されます。
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """
    ルートエンドポイント。

    運用時の簡易ステータスやドキュメント URL を返します。
    """
    return {
        "message": "Welcome to FastAPI Enterprise Application",
        "version": settings.version,
        "environment": settings.environment,
        "docs_url": f"{settings.api_prefix}/docs",
        "health_check": f"{settings.api_prefix}/health",
    }
