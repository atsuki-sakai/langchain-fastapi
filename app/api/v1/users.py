"""
ユーザー管理 API。

権限制御は依存関係(`Depends`)を用いて行います。
TypeScript での `router.get('/users', authMiddleware, handler)` に相当します。
Pydantic モデルで入出力のスキーマを明確にし、返却は統一のレスポンスラッパーで行います。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_superuser, get_current_user
from app.api.deps.database import get_db
from app.core.logging import get_logger
from app.models.base import BaseResponse, PaginatedResponse, PaginationParams
from app.models.user import User, UserCreate, UserInDB, UserUpdate
from app.services.user import (create_user, get_user_by_id, get_users,
                               update_user)

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=PaginatedResponse[User])
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """ユーザー一覧の取得（スーパーユーザー限定）。

    - ページング用に `page` と `size` を受け取ります
    - 実装簡略化のため `total` は取得件数から算出しています
    """
    try:
        pagination = PaginationParams(page=page, size=size)
        users = await get_users(db, skip=pagination.offset, limit=pagination.size)

        # 簡易実装: 実運用では総件数を COUNT などで別途取得してください
        total = len(users)

        # ORM → レスポンスモデル(Pydantic)に変換
        user_data = [User.from_orm(user) for user in users]

        return PaginatedResponse(
            success=True,
            message="Users retrieved successfully",
            data=user_data,
            meta={
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
                "pages": (total + pagination.size - 1) // pagination.size,
                "has_next": pagination.page * pagination.size < total,
                "has_prev": pagination.page > 1,
            },
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@router.post("", response_model=BaseResponse[User])
async def create_new_user(
    user_create: UserCreate,
    current_user: UserInDB = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """新規ユーザー作成（スーパーユーザー限定）。"""
    try:
        user = await create_user(db, user_create)

        logger.info(f"User created by {current_user.email}: {user.email}")

        return BaseResponse(
            success=True, message="User created successfully", data=User.from_orm(user)
        )

    except Exception as e:
        logger.error(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=BaseResponse[User])
async def get_user(
    user_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """ユーザー ID からユーザーを取得。

    - 本人か、またはスーパーユーザーのみが閲覧可能
    """
    try:
        # 本人以外はスーパーユーザーでないと閲覧不可
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return BaseResponse(
            success=True,
            message="User retrieved successfully",
            data=User.from_orm(user),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


@router.put("/{user_id}", response_model=BaseResponse[User])
async def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """ユーザー情報の更新。

    - 本人か、またはスーパーユーザーのみが更新可能
    - 一般ユーザーは `is_active` を変更できない
    """
    try:
        # 本人以外はスーパーユーザーでないと更新不可
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        # 一般ユーザーは is_active を変更不可
        if not current_user.is_superuser and user_update.is_active is not None:
            user_update.is_active = None

        updated_user = await update_user(db, user_id, user_update)

        logger.info(f"User updated by {current_user.email}: {user_id}")

        return BaseResponse(
            success=True,
            message="User updated successfully",
            data=User.from_orm(updated_user),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update failed for {user_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=BaseResponse[User])
async def get_current_user_profile(
    current_user: UserInDB = Depends(get_current_user),
) -> Any:
    """ログイン中ユーザーのプロフィール取得。"""
    return BaseResponse(
        success=True,
        message="Current user profile retrieved",
        data=User.from_orm(current_user),
    )


@router.put("/me", response_model=BaseResponse[User])
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """ログイン中ユーザーのプロフィール更新。

    - 自分自身の `is_active` は変更できないように強制無効化
    """
    try:
        # Users cannot change their own is_active status
        user_update.is_active = None

        updated_user = await update_user(db, current_user.id, user_update)

        logger.info(f"Profile updated by user: {current_user.email}")

        return BaseResponse(
            success=True,
            message="Profile updated successfully",
            data=User.from_orm(updated_user),
        )

    except Exception as e:
        logger.error(f"Profile update failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
