import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.models.user import UserCreate, UserInDB
from app.services.user import create_user
from main import app

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Test settings
def get_test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        app_name="Test FastAPI Application",
        environment="testing",
        debug=True,
        secret_key="test-secret-key-for-testing-only-minimum-32-chars",
        database_url=TEST_DATABASE_URL,
        cors_origins=["http://localhost:3000"],
    )

# Override dependency
app.dependency_overrides[get_settings] = get_test_settings


# Database fixtures
@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session):
    """Create async test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# User fixtures
@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPassword123",
        "password_confirm": "TestPassword123",
        "is_active": True
    }


@pytest.fixture
def superuser_data():
    """Superuser data."""
    return {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "password": "AdminPassword123",
        "password_confirm": "AdminPassword123",
        "is_active": True
    }


@pytest.fixture
async def test_user(db_session, test_user_data):
    """Create test user."""
    user_create = UserCreate(**test_user_data)
    user = await create_user(db_session, user_create)
    return user


@pytest.fixture
async def superuser(db_session, superuser_data):
    """Create superuser."""
    user_create = UserCreate(**superuser_data)
    user = await create_user(db_session, user_create)
    # Manually set as superuser (in real app, this would be done differently)
    user.is_superuser = True
    db_session.commit()
    return user


@pytest.fixture
def user_token(test_user_data):
    """Create user access token."""
    # In a real test, you'd create this with an actual user ID
    return create_access_token(subject="1")


@pytest.fixture
def superuser_token(superuser_data):
    """Create superuser access token."""
    # In a real test, you'd create this with an actual superuser ID
    return create_access_token(subject="2")


@pytest.fixture
def auth_headers(user_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def superuser_headers(superuser_token):
    """Create superuser authorization headers."""
    return {"Authorization": f"Bearer {superuser_token}"}


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()