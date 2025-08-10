"""
アプリ全体の例外ハンドリングを集約。

FastAPI の `@app.exception_handler` を用いて、例外 → 統一レスポンス(JSON)へ変換します。
TypeScript での `errorHandlingMiddleware` に相当し、構造化ログも併せて出力します。
"""

from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError as PydanticValidationError
from .exceptions import BaseAppException
from .logging import get_logger

logger = get_logger(__name__)


def create_error_response(
    message: str,
    status_code: int,
    details: dict = None,
    error_type: str = None,
) -> JSONResponse:
    """標準化されたエラーレスポンス(JSON)を作成。"""
    content = {
        "error": {
            "message": message,
            "type": error_type or "error",
            "details": details or {},
        }
    }
    
    return JSONResponse(
        status_code=status_code,
        content=content,
    )


def setup_error_handlers(app: FastAPI) -> None:
    """アプリにグローバル例外ハンドラを登録。"""
    
    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        """アプリ独自例外の処理。"""
        logger.error(
            "Application error",
            error_type=exc.__class__.__name__,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            path=str(request.url),
        )
        
        return create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            error_type=exc.__class__.__name__,
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """HTTP 例外の処理。"""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=str(request.url),
        )
        
        return create_error_response(
            message=exc.detail,
            status_code=exc.status_code,
            error_type="HTTPException",
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """リクエストバリデーションエラーの処理。"""
        logger.warning(
            "Validation error",
            errors=exc.errors(),
            path=str(request.url),
        )
        
        return create_error_response(
            message="Validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": exc.errors()},
            error_type="ValidationError",
        )
    
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
        """Pydantic バリデーションエラーの処理。"""
        logger.warning(
            "Pydantic validation error",
            errors=exc.errors(),
            path=str(request.url),
        )
        
        return create_error_response(
            message="Validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": exc.errors()},
            error_type="PydanticValidationError",
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """予期しない例外の処理。"""
        logger.error(
            "Unexpected error",
            error_type=exc.__class__.__name__,
            error=str(exc),
            path=str(request.url),
            exc_info=True,
        )
        
        return create_error_response(
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="InternalServerError",
        )