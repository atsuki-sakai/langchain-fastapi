"""
認証/認可 API。

ログイン、トークン発行/更新、ログインユーザー取得、パスワード変更を提供します。
TypeScript での `passport` や `next-auth` の役割に近いですが、
ここでは JWT を直接発行・検証します。
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.api.deps.database import get_db
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (create_access_token, create_refresh_token,
                               verify_token)
from app.models.base import BaseResponse
from app.models.user import (Token, TokenRefresh, User, UserChangePassword,
                             UserCreate, UserInDB, UserLogin)
from app.services.user import (authenticate_user, change_password, create_user,
                               get_user_by_id)

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


@router.post("/register", response_model=BaseResponse[User])
async def register(user_create: UserCreate, db: Session = Depends(get_db)) -> Any:
    """新規ユーザー登録。"""
    try:
        user = await create_user(db, user_create)
        logger.info(f"New user registered: {user.email}")

        return BaseResponse(
            success=True,
            message="User registered successfully",
            data=User.from_orm(user),
        )

    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=BaseResponse[Token])
async def login(user_login: UserLogin, db: Session = Depends(get_db)) -> Any:
    """ログインしてアクセストークン/リフレッシュトークンを発行。"""
    try:
        user = await authenticate_user(db, user_login.email, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Create tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )

        refresh_token = create_refresh_token(subject=str(user.id))

        token_data = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

        logger.info(f"User logged in: {user.email}")

        return BaseResponse(success=True, message="Login successful", data=token_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/login-form", response_model=BaseResponse[Token])
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Any:
    """OAuth2 のフォーム入力でログイン（SwaggerのTry it out用など）。"""
    try:
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )

        refresh_token = create_refresh_token(subject=str(user.id))

        token_data = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

        logger.info(f"User logged in via form: {user.email}")

        return BaseResponse(success=True, message="Login successful", data=token_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=BaseResponse[Token])
async def refresh_token(
    token_refresh: TokenRefresh, db: Session = Depends(get_db)
) -> Any:
    """リフレッシュトークンを用いてアクセストークンを再発行。"""
    try:
        # Verify refresh token
        payload = verify_token(token_refresh.refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Verify user still exists and is active
        user = await get_user_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=user_id, expires_delta=access_token_expires
        )

        # Optionally create new refresh token
        refresh_token = create_refresh_token(subject=user_id)

        token_data = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

        logger.info(f"Token refreshed for user: {user.email}")

        return BaseResponse(
            success=True, message="Token refreshed successfully", data=token_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not refresh token"
        )


@router.get("/me", response_model=BaseResponse[User])
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user),
) -> Any:
    """現在のログインユーザー情報を取得。"""
    return BaseResponse(
        success=True,
        message="User information retrieved",
        data=User.from_orm(current_user),
    )


@router.post("/change-password", response_model=BaseResponse[User])
async def change_user_password(
    password_change: UserChangePassword,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """現在のユーザーのパスワードを変更。"""
    try:
        updated_user = await change_password(db, current_user.id, password_change)

        logger.info(f"Password changed for user: {current_user.email}")

        return BaseResponse(
            success=True,
            message="Password changed successfully",
            data=User.from_orm(updated_user),
        )

    except Exception as e:
        logger.error(f"Password change failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
