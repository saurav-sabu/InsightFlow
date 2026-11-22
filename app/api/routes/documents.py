"""Document management endpoints for uploading, inspecting, and deleting collections."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import DocumentListResponse, DocumentUploadResponse
from app.core.document_processor import DocumentProcessor
from app.core.vector_store import VectorStoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """
    Upload a document (PDF, TXT, or CSV), chunk its content, and store it in Qdrant.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    logger.info(f"Processing uploaded file: '{file.filename}'")

    try:
        # 1. Extract and chunk text
        processor = DocumentProcessor()
        chunks = processor.process_upload(file.file, file.filename)

        if not chunks:
            raise HTTPException(status_code=400, detail="No content could be extracted from document")

        # 2. Store embeddings in Qdrant
        vector_store = VectorStoreService()
        doc_ids = vector_store.add_documents(chunks)

        logger.info(f"Successfully indexed '{file.filename}' with {len(chunks)} chunks.")

        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            filename=file.filename,
            chunks_created=len(chunks),
            document_ids=doc_ids,
        )

    except ValueError as e:
        logger.warning(f"File validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/info", response_model=DocumentListResponse)
async def get_collection_info() -> DocumentListResponse:
    """
    Get information and total document count of the vector store collection.
    """
    try:
        vector_store = VectorStoreService()
        info = vector_store.get_collection_info()

        return DocumentListResponse(
            collection_name=info["name"],
            total_documents=info["points_count"],
            status=info["status"],
        )
    except Exception as e:
        logger.error(f"Error retrieving collection info: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching collection info: {str(e)}")


@router.delete("/collection")
async def delete_collection() -> dict[str, str]:
    """
    Delete the entire document collection from Qdrant.
    """
    logger.warning("Request received to delete entire collection.")
    try:
        vector_store = VectorStoreService()
        vector_store.delete_collection()
        return {"message": "Collection deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")
