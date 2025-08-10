import pytest
from fastapi.testclient import TestClient
from app.core.config import get_settings

settings = get_settings()


@pytest.mark.integration
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get(f"{settings.api_prefix}/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == settings.version
        assert data["environment"] == settings.environment
    
    def test_register_user(self, client: TestClient):
        """Test user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "NewPassword123",
            "password_confirm": "NewPassword123",
            "is_active": True
        }
        
        response = client.post(f"{settings.api_prefix}/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User registered successfully"
        assert data["data"]["email"] == user_data["email"]
        assert data["data"]["username"] == user_data["username"]
        assert "id" in data["data"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user_data):
        """Test registration with duplicate email."""
        # First registration
        response1 = client.post(f"{settings.api_prefix}/v1/auth/register", json=test_user_data)
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        response2 = client.post(f"{settings.api_prefix}/v1/auth/register", json=test_user_data)
        assert response2.status_code == 400
    
    def test_login_success(self, client: TestClient, test_user_data):
        """Test successful login."""
        # First register user
        client.post(f"{settings.api_prefix}/v1/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post(f"{settings.api_prefix}/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post(f"{settings.api_prefix}/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_get_current_user_without_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get(f"{settings.api_prefix}/v1/auth/me")
        assert response.status_code == 403  # Should be unauthorized
    
    def test_get_current_user_with_token(self, client: TestClient, test_user_data):
        """Test getting current user with valid token."""
        # Register and login to get token
        client.post(f"{settings.api_prefix}/v1/auth/register", json=test_user_data)
        
        login_response = client.post(
            f"{settings.api_prefix}/v1/auth/login", 
            json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        token = login_response.json()["data"]["access_token"]
        
        # Use token to get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"{settings.api_prefix}/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user_data["email"]