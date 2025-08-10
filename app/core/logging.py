import logging
import structlog
import sys
from typing import Any, Dict
from .config import get_settings


def configure_logging() -> None:
    """Configure structured logging with structlog."""
    settings = get_settings()
    
    # Configure structlog
    timestamper = structlog.processors.TimeStamper(fmt="ISO")
    
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        # JSON formatter for production
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=False),
            foreign_pre_chain=shared_processors,
        )
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable formatter for development
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),
            foreign_pre_chain=shared_processors,
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
    """Get a configured logger instance."""
    return structlog.get_logger(name)


class LoggingMiddleware:
    """Middleware to add request ID and log requests."""
    
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
        
        # Log request start
        self.logger.info("Request started")
        
        # Process request
        await self.app(scope, receive, send)
        
        # Log request end
        self.logger.info("Request completed")