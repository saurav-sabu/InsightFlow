"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import documents, health, query
from app.config import get_settings
from app.utils.logger import get_logger, setup_logging

load_dotenv()
settings = get_settings()

# Explicitly ensure LangChain gets LangSmith tracing variables in os.environ
if settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    if settings.LANGSMITH_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    if settings.LANGSMITH_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT

setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

STATIC_DIR = Path("static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{__version__}")
    logger.info(f"LLM: {settings.LLM_MODEL} | Embeddings: {settings.EMBEDDING_MODEL}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description="""
## InsightFlow API

An enterprise Retrieval-Augmented Generation (RAG) platform built with:
- **FastAPI** for asynchronous API endpoints
- **LangChain (LCEL)** for RAG pipeline orchestration
- **Qdrant Cloud** for vector storage
- **Groq** for high-speed LLM inference
- **Google Gemini** for 768-dim embeddings
- **RAGAS** for automated answer quality evaluation
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder only if it exists (prevents startup crash if missing)
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register API routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/", tags=["Root"])
async def root():
    """Serve web UI if index.html exists in /static, otherwise return welcome JSON."""
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": __version__,
        "docs_url": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler returning standard JSON error responses."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
