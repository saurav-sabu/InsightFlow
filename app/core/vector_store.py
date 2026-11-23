"""Vector store module for Qdrant vector database operations."""

from functools import lru_cache
from typing import Any
from uuid import uuid4

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import get_settings
from app.core.embeddings import get_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Default embedding dimension (768 for Google text-embedding-004)
EMBEDDING_DIMENSION = 768


@lru_cache
def get_qdrant_client() -> QdrantClient:
    """Get or create a cached singleton QdrantClient instance."""
    logger.info(f"Connecting to Qdrant at: {settings.QDRANT_URL}")
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )


class VectorStoreService:
    """Manages document indexing, similarity search, and collection lifecycle in Qdrant."""

    def __init__(
        self,
        collection_name: str | None = None,
        vector_size: int = EMBEDDING_DIMENSION,
    ):
        """
        Initialize Qdrant client, embeddings, and ensure collection exists.
        """
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.vector_size = vector_size
        self.client = get_qdrant_client()
        self.embeddings = get_embeddings()

        # Ensure target collection is ready
        self._ensure_collection()

        # Wrap with LangChain's QdrantVectorStore interface
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        logger.info(f"VectorStoreService ready for collection '{self.collection_name}'")

    def _ensure_collection(self) -> None:
        """Create the collection if it does not already exist."""
        try:
            if not self.client.collection_exists(self.collection_name):
                logger.info(f"Creating collection '{self.collection_name}' (vector_size={self.vector_size})")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Collection '{self.collection_name}' created successfully.")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists.")
        except Exception as e:
            logger.warning(f"Could not verify or create collection: {e}")

    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add a list of Document objects to Qdrant with unique IDs."""
        if not documents:
            logger.warning("No documents provided to add.")
            return []

        ids = [str(uuid4()) for _ in documents]
        self.vector_store.add_documents(documents=documents, ids=ids)
        logger.info(f"Added {len(documents)} document chunk(s) to '{self.collection_name}'.")
        return ids

    def search(self, query: str, k: int | None = None) -> list[Document]:
        """Retrieve top-k similar documents for a query."""
        limit = k or settings.RETRIEVAL_K
        logger.debug(f"Searching for: '{query[:50]}' (k={limit})")
        return self.vector_store.similarity_search(query, k=limit)

    def search_with_scores(self, query: str, k: int | None = None) -> list[tuple[Document, float]]:
        """Retrieve top-k similar documents along with their similarity scores."""
        limit = k or settings.RETRIEVAL_K
        return self.vector_store.similarity_search_with_score(query, k=limit)

    def get_retriever(self, k: int | None = None) -> Any:
        """Return a LangChain retriever for building RAG chains."""
        limit = k or settings.RETRIEVAL_K
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": limit},
        )

    def get_collection_info(self) -> dict:
        """Get basic statistics about the current collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            logger.error(f"Error fetching collection info: {e}")
            return {"name": self.collection_name, "points_count": 0, "status": "unavailable"}

    def delete_collection(self) -> None:
        """Delete the current collection."""
        logger.warning(f"Deleting collection: {self.collection_name}")
        self.client.delete_collection(self.collection_name)

    def health_check(self) -> bool:
        """Check if Qdrant connection is alive."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
