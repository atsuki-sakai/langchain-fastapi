from fastapi import APIRouter
from .v1 import api_router as v1_router

# Create main API router
api_router = APIRouter()

# Include v1 router (no prefix since main.py already has /api/v1)
api_router.include_router(v1_router)

# You can add more versions here in the future
# api_router.include_router(v2_router, prefix="/v2")