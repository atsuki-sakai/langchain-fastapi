import time
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps.database import get_db
from app.core.config import get_settings
from app.models.base import HealthCheckResponse
from app.core.logging import get_logger

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)

# Store application start time
start_time = time.time()


@router.get("", response_model=HealthCheckResponse)
@router.get("/", response_model=HealthCheckResponse)
async def health_check() -> Any:
    """Basic health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
        environment=settings.environment,
        uptime=time.time() - start_time
    )


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check(db: Session = Depends(get_db)) -> Any:
    """Readiness check including database connectivity."""
    try:
        # Test database connection with proper SQLAlchemy 2.x text() usage
        result = db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        logger.info(f"Database connectivity test successful: {test_result}")
        
        return HealthCheckResponse(
            status="ready",
            timestamp=datetime.utcnow(),
            version=settings.version,
            environment=settings.environment,
            uptime=time.time() - start_time
        )
    
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            status="not_ready",
            timestamp=datetime.utcnow(),
            version=settings.version,
            environment=settings.environment,
            uptime=time.time() - start_time
        )


@router.get("/live", response_model=HealthCheckResponse)
async def liveness_check() -> Any:
    """Liveness check to verify application is running."""
    return HealthCheckResponse(
        status="alive",
        timestamp=datetime.utcnow(),
        version=settings.version,
        environment=settings.environment,
        uptime=time.time() - start_time
    )