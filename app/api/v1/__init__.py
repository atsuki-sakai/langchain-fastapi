from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .health import router as health_router

# Create main API v1 router
api_router = APIRouter()

# Include all routers with their prefixes
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)