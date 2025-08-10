"""
LLM サービス層。LangChain を用いてチャット応答を生成します。
OpenAI / OpenRouter を切り替え対応。
"""

from typing import List

from langchain_core.messages import (AIMessage, BaseMessage, HumanMessage,
                                     SystemMessage)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.llm import ChatMessage, ChatRequest, ChatResponse

logger = get_logger(__name__)


def _to_langchain_messages(
    system_prompt: str | None,
    history: List[ChatMessage] | None,
    user_message: str,
) -> List[BaseMessage]:
    messages: List[BaseMessage] = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    if history:
        for item in history:
            if item.role == "system":
                messages.append(SystemMessage(content=item.content))
            elif item.role == "user":
                messages.append(HumanMessage(content=item.content))
            else:
                messages.append(AIMessage(content=item.content))

    messages.append(HumanMessage(content=user_message))
    return messages


def _build_openai_llm(model_name: str, temperature: float):
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=model_name,
        temperature=temperature,
    )


def _build_openrouter_llm(model_name: str, temperature: float):
    # OpenRouter は OpenAI 互換の HTTP API を提供。
    # LangChain の ChatOpenAI に base_url と api_key を渡して利用可能。
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")

    default_model = settings.openrouter_model or "openrouter/auto"
    target_model = model_name or default_model

    # OpenRouter用の追加ヘッダ（任意）
    default_headers = {}
    if settings.openrouter_referer:
        default_headers["HTTP-Referer"] = settings.openrouter_referer
    if settings.openrouter_app_title:
        default_headers["X-Title"] = settings.openrouter_app_title

    return ChatOpenAI(
        api_key=settings.openrouter_api_key,
        model=target_model,
        base_url=settings.openrouter_base_url,
        temperature=temperature,
        default_headers=default_headers or None,
    )


async def generate_chat_response(req: ChatRequest) -> ChatResponse:
    """プロバイダを切り替えてチャット応答を生成。"""
    settings = get_settings()

    provider = (req.provider or "openrouter").lower()

    if provider == "openrouter":
        model_name = req.model or settings.openrouter_model or "openrouter/auto"
        llm = _build_openrouter_llm(model_name, req.temperature or 0.2)
    else:
        model_name = req.model or settings.openai_model or "gpt-4o-mini"
        llm = _build_openai_llm(model_name, req.temperature or 0.2)

    messages = _to_langchain_messages(req.system, req.history, req.message)

    logger.info("Invoking LLM", extra={"provider": provider, "model": model_name})
    result = await llm.ainvoke(messages)

    return ChatResponse(content=result.content, model=model_name)
