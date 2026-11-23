"""Embedding generation module for converting text into vector representations."""

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache
def get_embeddings() -> Embeddings:
    """
    Get or create a cached embeddings instance.
    Uses Google Gemini embeddings matching your .env and requirements.
    """
    settings = get_settings()
    logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL}")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        output_dimensionality=768,  # Match Qdrant collection dimension
    )

    logger.info("Embedding model initialized successfully.")
    return embeddings


class EmbeddingService:
    """Convenience service for generating query and document embeddings."""

    def __init__(self, embeddings: Embeddings | None = None):
        """Initialize with an optional embeddings instance or use the cached default."""
        self.embeddings = embeddings or get_embeddings()

    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding vector for a single search query."""
        logger.debug(f"Embedding query: {text[:50]}...")
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple document chunks."""
        logger.debug(f"Embedding {len(texts)} document chunk(s)")
        return self.embeddings.embed_documents(texts)
