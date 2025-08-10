"""
セキュリティ関連のユーティリティ。

- パスワードハッシュ化/検証（bcrypt）
- JWT の発行/検証（アクセス/リフレッシュ/パスワードリセット）

TypeScript での `bcrypt` と `jsonwebtoken` に相当します。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings
from .exceptions import UnauthorizedError

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """アクセストークン(JWT)を生成。"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """リフレッシュトークン(JWT)を生成。"""
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """JWT を検証してペイロードを返す。

    token_type が一致しない場合や期限切れの場合は `UnauthorizedError`。
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # Check token type
        if payload.get("type") != token_type:
            raise UnauthorizedError("Invalid token type")

        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise UnauthorizedError("Token has expired")

        return payload

    except JWTError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}")


def get_user_id_from_token(token: str) -> str:
    """トークンからユーザーID(`sub`)を取り出す。"""
    payload = verify_token(token)
    user_id = payload.get("sub")

    if user_id is None:
        raise UnauthorizedError("Invalid token: no user ID")

    return user_id


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュの照合。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードからハッシュを生成。"""
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """パスワードリセット用の JWT を生成。"""
    expire = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes validity

    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "password_reset",
    }

    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return token


def verify_password_reset_token(token: str) -> str:
    """パスワードリセットトークンを検証し、メールアドレスを返す。"""
    payload = verify_token(token, token_type="password_reset")
    email = payload.get("sub")

    if email is None:
        raise UnauthorizedError("Invalid token: no email")

    return email
