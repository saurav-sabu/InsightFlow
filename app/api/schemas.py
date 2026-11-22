"""Pydantic schemas for FastAPI request and response validation."""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health & Status Schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Basic health check status."""
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReadinessResponse(BaseModel):
    """Readiness probe indicating if Qdrant vector database is reachable."""
    status: str
    qdrant_connected: bool
    collection_info: dict[str, Any]


# ---------------------------------------------------------------------------
# Document Ingestion Schemas
# ---------------------------------------------------------------------------

class DocumentUploadResponse(BaseModel):
    """Response returned after uploading and indexing a document."""
    message: str
    filename: str
    chunks_created: int
    document_ids: list[str]


class DocumentListResponse(BaseModel):
    """Statistics and point counts for the vector collection."""
    collection_name: str
    total_documents: int
    status: str


# ---------------------------------------------------------------------------
# Query & RAG Schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Request payload for asking questions via the RAG pipeline."""
    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    include_sources: bool = True
    enable_evaluation: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What is RAG?",
                    "include_sources": True,
                    "enable_evaluation": False,
                }
            ]
        }
    }


class SourceDocument(BaseModel):
    """Retrieved document excerpt and its source metadata."""
    content: str
    metadata: dict[str, Any] = {}


class EvaluationScores(BaseModel):
    """RAGAS metrics assessing answer quality."""
    faithfulness: float | None = Field(default=None, ge=0.0, le=1.0)
    answer_relevancy: float | None = Field(default=None, ge=0.0, le=1.0)
    evaluation_time_ms: float | None = None
    error: str | None = None


class QueryResponse(BaseModel):
    """Generated answer accompanied by retrieval metadata and optional evaluation."""
    question: str
    answer: str
    sources: list[SourceDocument] | None = None
    processing_time_ms: float
    evaluation: EvaluationScores | None = None


# ---------------------------------------------------------------------------
# Error Schemas
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    detail: str | None = None
