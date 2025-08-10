"""
Pydantic ベースの共通スキーマとレスポンスラッパー。

TypeScript の `zod` スキーマと DTO、共通レスポンス型に近い役割を持ちます。
"""

from typing import Generic, TypeVar, Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Type variable for generic responses
DataT = TypeVar('DataT')


class BaseSchema(BaseModel):
    """共通設定を持つ基底スキーマ。"""
    
    model_config = ConfigDict(
        # Allow population by field name (for compatibility)
        populate_by_name=True,
        # Use enum values instead of enum names
        use_enum_values=True,
        # Validate assignment to ensure data integrity
        validate_assignment=True,
        # Allow arbitrary types (useful for complex objects)
        arbitrary_types_allowed=True,
        # SQLAlchemy 等の ORM オブジェクトからの読み取りを許可（Pydantic v2）
        from_attributes=True,
    )


class TimestampSchema(BaseSchema):
    """作成・更新時刻を含む共通スキーマ。"""
    
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class PaginationParams(BaseSchema):
    """ページング用の標準パラメータ。"""
    
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """DB クエリ用のオフセットを算出。"""
        return (self.page - 1) * self.size


class PaginationMeta(BaseSchema):
    """ページングメタ情報。"""
    
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class BaseResponse(BaseModel, Generic[DataT]):
    """汎用レスポンスラッパー。"""
    
    success: bool = Field(default=True, description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[DataT] = Field(None, description="Response data")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """ページング対応レスポンスラッパー。"""
    
    success: bool = Field(default=True, description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: List[DataT] = Field(description="List of items")
    meta: PaginationMeta = Field(description="Pagination metadata")


class ErrorResponse(BaseSchema):
    """エラーレスポンススキーマ。"""
    
    success: bool = Field(default=False, description="Whether the request was successful")
    error: dict = Field(description="Error details")


class HealthCheckResponse(BaseSchema):
    """ヘルスチェックのレスポンススキーマ。"""
    
    status: str = Field(description="Service status")
    timestamp: datetime = Field(description="Check timestamp")
    version: str = Field(description="API version")
    environment: str = Field(description="Environment name")
    uptime: Optional[float] = Field(None, description="Uptime in seconds")


# Utility functions for response creation
def create_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    success: bool = True,
) -> BaseResponse:
    """標準レスポンスを生成。"""
    return BaseResponse(
        success=success,
        message=message,
        data=data,
    )


def create_paginated_response(
    data: List[Any],
    pagination: PaginationParams,
    total: int,
    message: Optional[str] = None,
) -> PaginatedResponse:
    """ページングレスポンスを生成。"""
    pages = (total + pagination.size - 1) // pagination.size
    
    meta = PaginationMeta(
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=pages,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1,
    )
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        meta=meta,
    )