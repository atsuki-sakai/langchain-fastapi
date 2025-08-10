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
    """Create standardized error response."""
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
    """Setup global error handlers for the FastAPI app."""
    
    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        """Handle custom application exceptions."""
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
        """Handle HTTP exceptions."""
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
        """Handle request validation errors."""
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
        """Handle Pydantic validation errors."""
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
        """Handle unexpected exceptions."""
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