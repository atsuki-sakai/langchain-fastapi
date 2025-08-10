from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import verify_token, get_user_id_from_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.models.user import User, UserInDB
from app.api.deps.database import get_db
from app.services.user import get_user_by_id

# HTTP Bearer token dependency
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user ID from JWT token."""
    try:
        token = credentials.credentials
        user_id = get_user_id_from_token(token)
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> UserInDB:
    """Get current authenticated user."""
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
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active"
        )
    return current_user


async def get_current_superuser(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current user if they are a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_permissions(*permissions: str):
    """Decorator to require specific permissions."""
    def permission_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        # In a real implementation, you would check user permissions here
        # For now, we'll just check if the user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not active"
            )
        
        # Example permission check (would be implemented based on your permission system)
        # user_permissions = get_user_permissions(current_user.id)
        # if not all(perm in user_permissions for perm in permissions):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Insufficient permissions"
        #     )
        
        return current_user
    
    return permission_checker


class OptionalAuth:
    """Optional authentication dependency."""
    
    def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[str]:
        """Get user ID if token is provided, None otherwise."""
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            user_id = get_user_id_from_token(token)
            return user_id
        except Exception:
            return None


optional_auth = OptionalAuth()