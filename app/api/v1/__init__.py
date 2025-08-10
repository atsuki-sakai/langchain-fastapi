"""
API v1 のルーター集合。

このモジュールでは、`/auth`、`/users`、`/health` の各機能を
それぞれ独立したルーターとしてまとめ、`api_router` に統合します。
`main.py` で `/api/v1` が付与されるため、実際のエンドポイントは
`/api/v1/auth`、`/api/v1/users`、`/api/v1/health` となります。
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .health import router as health_router
from .llm import router as llm_router
from .users import router as users_router

# v1 のメインルーター
api_router = APIRouter()

# 各ドメインルーターを取り込み
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])

api_router.include_router(users_router, prefix="/users", tags=["users"])

api_router.include_router(health_router, prefix="/health", tags=["health"])

api_router.include_router(llm_router, prefix="/llm", tags=["langchain"])
