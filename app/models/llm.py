"""
LangChain/LLM 機能のDTO（Pydanticモデル）。
"""

from typing import List, Literal, Optional

from pydantic import Field

from app.models.base import BaseSchema


class ChatMessage(BaseSchema):
    """チャット履歴の単一メッセージ。"""

    role: Literal["system", "user", "assistant"] = Field(description="Message role")
    content: str = Field(description="Message content")


class ChatRequest(BaseSchema):
    """チャット生成の入力。"""

    message: str = Field(description="Current user message")
    system: Optional[str] = Field(default=None, description="System instruction prompt")
    history: Optional[List[ChatMessage]] = Field(
        default=None, description="Previous conversation history"
    )
    model: Optional[str] = Field(default=None, description="Override model name")
    provider: Optional[Literal["openai", "openrouter"]] = Field(
        default=None, description="LLM provider selector"
    )
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0)


class ChatResponse(BaseSchema):
    """チャット生成の出力。"""

    content: str = Field(description="Generated assistant reply")
    model: str = Field(description="Model used")


class BlogArticleRequest(BaseSchema):
    """キーワードからブログ記事を生成するための入力。"""

    keyword: str = Field(description="ブログ記事の元となるキーワード")
    language: Literal["ja", "en"] = Field(default="ja", description="生成言語")
    target_audience: Optional[str] = Field(default=None, description="想定読者像")
    writing_style: Optional[str] = Field(default=None, description="文体やトーンの指示")
    section_count: int = Field(default=4, ge=3, le=8, description="セクション数")
    provider: Optional[Literal["openai", "openrouter"]] = Field(
        default=None, description="LLMプロバイダの選択"
    )
    model: Optional[str] = Field(default=None, description="モデルの上書き")
    clarification_answers: Optional[list[str]] = Field(
        default=None, description="前回の確認質問に対する回答"
    )


class BlogSection(BaseSchema):
    """単一セクションのデータ。"""

    title: str = Field(description="セクションタイトル")
    content: str = Field(description="本文（約1000文字）")


class BlogArticleResponse(BaseSchema):
    """ブログ生成の結果。必要なら追加の確認質問も返す。"""

    need_clarification: bool = Field(description="追加の確認が必要か")
    questions: Optional[list[str]] = Field(default=None, description="確認質問の一覧")
    title: Optional[str] = Field(default=None, description="記事タイトル")
    outline: Optional[list[str]] = Field(
        default=None, description="セクション見出しの一覧"
    )
    sections: Optional[list[BlogSection]] = Field(
        default=None, description="各セクション"
    )
    final_article: Optional[str] = Field(default=None, description="編集後の最終記事")
