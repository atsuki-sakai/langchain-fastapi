"""
認証・認可に関する依存関係（Dependency）。

FastAPI では `Depends(...)` を通じて前処理（ミドルウェアに近い）を
エンドポイント関数に差し込めます。TypeScript のミドルウェアチェーンと
似ていますが、関数の引数解決（DI）に統合されている点が特徴です。
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.core.security import get_user_id_from_token
from app.models.user import UserInDB
from app.services.user import get_user_by_id

# HTTP Bearer token dependency (optional)
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """JWT からユーザーIDを取得。

    Authorization: Bearer <token> を想定し、JWT を検証して `sub` を返します。
    失敗時は 401 を返します。
    """
    try:
        token = credentials.credentials
        user_id = get_user_id_from_token(token)
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)
) -> UserInDB:
    """現在ログイン中のユーザーを返す。

    - ユーザーが存在しない/非アクティブなら 401
    """
    user = await get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active",
        )

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """アクティブなログインユーザーのみ許可。"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active"
        )
    return current_user


async def get_current_superuser(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """スーパーユーザーのみ許可。"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def require_permissions(*permissions: str):
    """簡易パーミッションチェックのデコレータファクトリ。

    実運用ではユーザー権限の集合と照合してください。
    """

    def permission_checker(
        current_user: UserInDB = Depends(get_current_user),
    ) -> UserInDB:
        # In a real implementation, you would check user permissions here
        # For now, we'll just check if the user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not active",
            )

        # Example permission check
        # user_permissions = get_user_permissions(current_user.id)
        # if not all(perm in user_permissions for perm in permissions):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Insufficient permissions",
        #     )

        return current_user

    return permission_checker


class OptionalAuth:
    """任意認証の依存関係。

    トークンがあれば検証し `user_id` を返し、無ければ `None` を返します。
    """

    def __call__(
        self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[str]:
        """トークンがあれば user_id、無ければ None を返す。"""
        if not credentials:
            return None

        try:
            token = credentials.credentials
            user_id = get_user_id_from_token(token)
            return user_id
        except Exception:
            return None


optional_auth = OptionalAuth()
