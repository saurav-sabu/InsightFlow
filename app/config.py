from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    GROQ_API_KEY: str
    GOOGLE_API_KEY: str
    OPENAI_API_KEY: str | None = None

    # Qdrant Cloud Configuration
    QDRANT_URL: str
    QDRANT_API_KEY: str
    COLLECTION_NAME: str = "insightflow_documents"

    # Document Processing Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Model Configuration
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_TEMPERATURE: float = 0.0

    # Retrieval Settings
    RETRIEVAL_K: int = 4

    # Logging
    LOG_LEVEL: str = "INFO"

    # LangSmith Tracing (Optional)
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str | None = None

    # RAGAS Evaluation Settings
    ENABLE_RAGAS_EVALUATION: bool = True
    RAGAS_TIMEOUT_SECONDS: float = 30.0
    RAGAS_LOG_RESULTS: bool = True
    RAGAS_LLM_MODEL: str | None = None
    RAGAS_LLM_TEMPERATURE: float | None = None
    RAGAS_EMBEDDING_MODEL: str | None = None

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Application Info
    APP_NAME: str = "InsightFlow"
    APP_VERSION: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings()


# Export ready-to-use instance
settings = get_settings()
