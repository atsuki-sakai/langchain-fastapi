import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security import (create_access_token, get_password_hash,
                               verify_password, verify_token)


class TestSecurity:
    """Test security functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        # Password should be hashed
        assert hashed != password
        assert len(hashed) > 20

        # Verification should work
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_access_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        user_id = "123"
        token = create_access_token(subject=user_id)

        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 20

        # Token verification should work
        payload = verify_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_invalid_token_verification(self):
        """Test invalid token verification."""
        with pytest.raises(UnauthorizedError):
            verify_token("invalid_token")

    def test_wrong_token_type(self):
        """Test wrong token type verification."""
        user_id = "123"
        token = create_access_token(subject=user_id)

        with pytest.raises(UnauthorizedError, match="Invalid token type"):
            verify_token(token, token_type="refresh")
