"""
LLM / LangChain エンドポイント。

- POST /api/v1/llm/chat: チャット応答生成
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import optional_auth
from app.core.logging import get_logger
from app.models.base import BaseResponse
from app.models.llm import (BlogArticleRequest, BlogArticleResponse,
                            ChatRequest, ChatResponse)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=BaseResponse[ChatResponse])
async def chat(
    req: ChatRequest,
    user_id: str | None = Depends(optional_auth),
) -> Any:
    """LLMでチャット応答を生成。

    認証は任意。トークンがあれば `user_id` を取得して監査ログに記録します。
    """
    try:
        # 遅延インポートで依存パッケージ未導入時のテスト失敗を回避
        from app.services.llm import generate_chat_response

        resp = await generate_chat_response(req)
        logger.info("LLM chat generated", extra={"user_id": user_id})
        return BaseResponse(success=True, message="ok", data=resp)
    except ValueError as e:
        # 設定や入力の問題は 400 を返す
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"LLM chat error: {str(e)}", exc_info=True)
        # 依存未導入(ImportError)等の詳細を返す
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/blog/generate", response_model=BaseResponse[BlogArticleResponse])
async def generate_blog(
    req: BlogArticleRequest,
    user_id: str | None = Depends(optional_auth),
) -> Any:
    """キーワードからブログ記事を段階的に生成するサンプル実装。

    - 意図の把握（曖昧なら確認質問）
    - アウトライン作成（セクション数はデフォルト4）
    - 各セクションを約1000文字で執筆
    - 編集者視点の校正で最終記事を返す

    コメント多めでLangChain学習に向いた書き方にしています。
    """
    try:
        # 遅延インポートで依存パッケージ未導入時のテスト失敗を回避
        from app.services.langchain_blog import generate_blog_article

        result = await generate_blog_article(req)
        logger.info(
            "Blog generated", extra={"user_id": user_id, "keyword": req.keyword}
        )
        return BaseResponse(success=True, message="ok", data=result)
    except ValueError as e:
        # 設定や入力の問題は 400 を返す
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Blog generation error: {str(e)}", exc_info=True)
        # 依存未導入(ImportError)等の詳細を返す
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
