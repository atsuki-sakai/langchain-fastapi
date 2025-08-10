"""
構造化ロギングの設定とミドルウェア。

`structlog` を使い、JSON 形式のログや開発向けのリッチ表示を切り替えます。
TypeScript の `pino` や `winston` に相当する仕組みです。
"""

import logging
import structlog
import sys
from typing import Any, Dict
from .config import get_settings


def configure_logging() -> None:
    """`structlog` を用いた構造化ロギングを初期化。"""
    settings = get_settings()
    
    # Configure structlog
    timestamper = structlog.processors.TimeStamper(fmt="ISO")
    
    # structlog 側のプロセッサチェーン（stdlib の ProcessorFormatter とは分離）
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        # stdlib のフォーマッタはできるだけ素朴に（構造化は structlog 側で）
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=False),
        )
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),
        )
        shared_processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Suppress unnecessary logs
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """構成済みロガーを取得。"""
    return structlog.get_logger(name)


class LoggingMiddleware:
    """リクエストIDを付与してリクエスト開始/終了を記録するミドルウェア。"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Add request ID to context
        import uuid
        request_id = str(uuid.uuid4())
        
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=scope["method"],
            path=scope["path"],
        )
        
        # リクエスト開始
        self.logger.info("Request started")
        
        # Process request
        await self.app(scope, receive, send)
        
        # リクエスト終了
        self.logger.info("Request completed")