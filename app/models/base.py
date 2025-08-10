from typing import Generic, TypeVar, Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Type variable for generic responses
DataT = TypeVar('DataT')


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        # Allow population by field name (for compatibility)
        populate_by_name=True,
        # Use enum values instead of enum names
        use_enum_values=True,
        # Validate assignment to ensure data integrity
        validate_assignment=True,
        # Allow arbitrary types (useful for complex objects)
        arbitrary_types_allowed=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class PaginationParams(BaseSchema):
    """Standard pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class PaginationMeta(BaseSchema):
    """Pagination metadata."""
    
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class BaseResponse(BaseModel, Generic[DataT]):
    """Generic response wrapper."""
    
    success: bool = Field(default=True, description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[DataT] = Field(None, description="Response data")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated response wrapper."""
    
    success: bool = Field(default=True, description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: List[DataT] = Field(description="List of items")
    meta: PaginationMeta = Field(description="Pagination metadata")


class ErrorResponse(BaseSchema):
    """Error response schema."""
    
    success: bool = Field(default=False, description="Whether the request was successful")
    error: dict = Field(description="Error details")


class HealthCheckResponse(BaseSchema):
    """Health check response schema."""
    
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
    """Create a standard response."""
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
    """Create a paginated response."""
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