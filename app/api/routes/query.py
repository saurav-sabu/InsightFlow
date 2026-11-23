"""Query endpoints for RAG Q&A, token streaming, and vector similarity search."""

import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    EvaluationScores,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)
from app.core.rag_chain import RAGChain
from app.core.vector_store import VectorStoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Ask a question and receive an AI-generated answer based on indexed documents.
    Optionally returns source citations and RAGAS quality evaluation.
    """
    logger.info(
        f"Received query: '{request.question[:80]}' "
        f"(sources={request.include_sources}, eval={request.enable_evaluation})"
    )
    start_time = time.time()

    try:
        rag_chain = RAGChain()
        sources = None
        evaluation = None

        # 1. Query with RAGAS quality assessment
        if request.enable_evaluation:
            result = await rag_chain.aquery_with_evaluation(request.question)
            answer = result["answer"]
            evaluation = EvaluationScores(**result["evaluation"])
            if request.include_sources:
                sources = [SourceDocument(**s) for s in result["sources"]]

        # 2. Query with retrieved source documents
        elif request.include_sources:
            result = await rag_chain.aquery_with_sources(request.question)
            answer = result["answer"]
            sources = [SourceDocument(**s) for s in result["sources"]]

        # 3. Simple answer generation only
        else:
            answer = await rag_chain.aquery(request.question)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Query completed in {elapsed_ms}ms")

        return QueryResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            processing_time_ms=elapsed_ms,
            evaluation=evaluation,
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {e!s}") from e


@router.post("/stream")
async def query_stream(request: QueryRequest) -> StreamingResponse:
    """
    Stream generated response tokens in real-time as plain text.
    """
    logger.info(f"Streaming query: '{request.question[:80]}'")
    try:
        rag_chain = RAGChain()

        def token_generator():
            try:
                yield from rag_chain.stream(request.question)
            except Exception as e:
                logger.error(f"Error in token generator: {e}")
                yield f"\n\n[Error: {e!s}]"

        return StreamingResponse(token_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Error initializing stream: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {e!s}") from e


@router.post("/search")
async def search_documents(request: QueryRequest) -> dict:
    """
    Perform vector similarity search and return relevant document chunks with relevance scores.
    """
    logger.info(f"Searching documents for: '{request.question[:80]}'")
    try:
        vector_store = VectorStoreService()
        results = vector_store.search_with_scores(request.question)

        documents = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": round(score, 4),
            }
            for doc, score in results
        ]

        return {
            "query": request.question,
            "count": len(documents),
            "results": documents,
        }

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}") from e
