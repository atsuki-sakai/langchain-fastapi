from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr, Field, validator
from .base import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(description="User email address")
    username: str = Field(min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    is_active: bool = Field(default=True, description="Whether the user is active")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserCreate(UserBase):
    """Schema for user creation."""
    
    password: str = Field(min_length=8, max_length=128, description="Password")
    password_confirm: str = Field(description="Password confirmation")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseSchema):
    """Schema for user updates."""
    
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")


class UserInDB(UserBase, TimestampSchema):
    """User schema as stored in database."""
    
    id: int = Field(description="User ID")
    hashed_password: str = Field(description="Hashed password")
    is_superuser: bool = Field(default=False, description="Whether the user is a superuser")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        orm_mode = True


class User(UserBase, TimestampSchema):
    """User schema for API responses."""
    
    id: int = Field(description="User ID")
    is_superuser: bool = Field(default=False, description="Whether the user is a superuser")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        orm_mode = True


class UserLogin(BaseSchema):
    """Schema for user login."""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="Password")
    remember_me: bool = Field(default=False, description="Whether to remember the login")


class UserChangePassword(BaseSchema):
    """Schema for password change."""
    
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, max_length=128, description="New password")
    new_password_confirm: str = Field(description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class TokenPayload(BaseSchema):
    """JWT token payload schema."""
    
    sub: Optional[str] = None  # subject (user ID)
    exp: Optional[int] = None  # expiration time
    iat: Optional[int] = None  # issued at
    type: Optional[str] = None  # token type


class Token(BaseSchema):
    """Token response schema."""
    
    access_token: str = Field(description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenRefresh(BaseSchema):
    """Token refresh request schema."""
    
    refresh_token: str = Field(description="Refresh token")