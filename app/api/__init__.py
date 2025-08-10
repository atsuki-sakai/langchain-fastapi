"""
API ルーターのエントリーポイント。

このモジュールはアプリ全体の API ルーティングを集約します。
`main.py` 側で `/api/v1` のプレフィックスを付与しているため、
ここでは v1 のルーターをそのまま取り込みます。
今後 v2 以降を追加する場合は、同様にここでルーターを登録します。
"""

from fastapi import APIRouter
from .v1 import api_router as v1_router

# アプリ全体のメイン API ルーター
api_router = APIRouter()

# v1 ルーターの取り込み
# テストの期待に合わせ、`/api/v1` で到達できるようにしています。
api_router.include_router(v1_router)

# 例: 将来バージョンの追加
# from .v2 import api_router as v2_router
# api_router.include_router(v2_router, prefix="/v2")