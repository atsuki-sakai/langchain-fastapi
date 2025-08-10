"""
ヘルスチェック関連のエンドポイント。

Kubernetes 等のヘルスチェック/レディネス/ライブネスに対応するため
`/health`、`/health/ready`、`/health/live` を提供します。
TypeScript/Express での単純な `GET /health` と同様ですが、
ここでは Pydantic モデルを用いて厳密なレスポンススキーマを返します。
"""

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.base import HealthCheckResponse

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)

# Store application start time
start_time = time.time()  # アプリ起動時刻を保持し uptime を計算


@router.get("", response_model=HealthCheckResponse)
@router.get("/", response_model=HealthCheckResponse, include_in_schema=False)
async def health_check() -> Any:
    """基本的なヘルスチェック。

    - アプリが動作していること
    - バージョンや環境情報
    - 稼働時間(uptime)
    を返します。
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
        environment=settings.environment,
        uptime=time.time() - start_time,
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check(db: Session = Depends(get_db)) -> Any:
    """レディネスチェック（DB 接続確認を含む）。

    DB へ `SELECT 1` を発行して接続性を確認します。
    失敗した場合でも 200 を返す仕様にしているため、
    実運用では適宜 503 などに変更してください。
    """
    try:
        # Test database connection with proper SQLAlchemy 2.x text() usage
        result = db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        logger.info(f"Database connectivity test successful: {test_result}")

        return HealthCheckResponse(
            status="ready",
            timestamp=datetime.utcnow(),
            version=settings.version,
            environment=settings.environment,
            uptime=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            status="not_ready",
            timestamp=datetime.utcnow(),
            version=settings.version,
            environment=settings.environment,
            uptime=time.time() - start_time,
        )


@router.get("/live", response_model=HealthCheckResponse)
async def liveness_check() -> Any:
    """ライブネスチェック。

    アプリプロセスが応答するかのみを確認します。
    """
    return HealthCheckResponse(
        status="alive",
        timestamp=datetime.utcnow(),
        version=settings.version,
        environment=settings.environment,
        uptime=time.time() - start_time,
    )
