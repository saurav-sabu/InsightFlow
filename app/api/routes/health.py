"""Health and readiness check endpoints."""

from fastapi import APIRouter, HTTPException

from app.api.schemas import HealthResponse, ReadinessResponse
from app.config import get_settings
from app.core.vector_store import VectorStoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic liveness probe confirming the FastAPI service is running.
    """
    logger.debug("Liveness probe requested.")
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe verifying vector database (Qdrant) connectivity.
    """
    logger.debug("Readiness check requested.")
    try:
        vector_store = VectorStoreService()
        if not vector_store.health_check():
            raise HTTPException(status_code=503, detail="Vector database is unreachable")

        return ReadinessResponse(
            status="ready",
            qdrant_connected=True,
            collection_info=vector_store.get_collection_info(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")
