"""RAGAS evaluation module for evaluating RAG response quality (faithfulness and relevance)."""

import asyncio
import time
from typing import Any

from datasets import Dataset
from langchain_groq import ChatGroq
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, faithfulness

from app.config import get_settings
from app.core.embeddings import get_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGASEvaluator:
    """Evaluates RAG generation quality using reference-free RAGAS metrics."""

    def __init__(self):
        """Initialize models and metrics using the application settings."""
        self.settings = get_settings()

        llm_model = self.settings.RAGAS_LLM_MODEL or self.settings.LLM_MODEL
        temperature = (
            self.settings.RAGAS_LLM_TEMPERATURE
            if self.settings.RAGAS_LLM_TEMPERATURE is not None
            else self.settings.LLM_TEMPERATURE
        )

        # Initialize Groq LLM and Gemini Embeddings with Ragas wrappers
        groq_chat = ChatGroq(
            model=llm_model,
            temperature=temperature,
            api_key=self.settings.GROQ_API_KEY,
        )
        self.llm = LangchainLLMWrapper(groq_chat)
        self.embeddings = LangchainEmbeddingsWrapper(get_embeddings())

        # Reference-free evaluation metrics
        self.metrics = [faithfulness, answer_relevancy]

        logger.info(f"RAGASEvaluator initialized with LLM: '{llm_model}'")

    async def aevaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> dict[str, Any]:
        """
        Asynchronously evaluate a query, generated answer, and retrieved contexts.
        Returns faithfulness and answer_relevancy scores.
        """
        logger.info(f"Starting RAGAS evaluation for: '{question[:60]}'...")
        start_time = time.time()

        try:
            # Build Dataset in the format RAGAS expects
            dataset = Dataset.from_dict({
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            })

            # Run synchronous evaluate() in a non-blocking thread pool
            result = await asyncio.to_thread(
                evaluate,
                dataset=dataset,
                metrics=self.metrics,
                llm=self.llm,
                embeddings=self.embeddings,
            )

            # Extract result scores
            row = result.to_pandas().to_dict("records")[0]
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            scores = {
                "faithfulness": round(float(row["faithfulness"]), 4) if "faithfulness" in row and row["faithfulness"] is not None else None,
                "answer_relevancy": round(float(row["answer_relevancy"]), 4) if "answer_relevancy" in row and row["answer_relevancy"] is not None else None,
                "evaluation_time_ms": elapsed_ms,
                "error": None,
            }

            if self.settings.RAGAS_LOG_RESULTS:
                logger.info(
                    f"RAGAS evaluation completed in {elapsed_ms}ms: "
                    f"faithfulness={scores['faithfulness']}, relevancy={scores['answer_relevancy']}"
                )
            return scores

        except Exception as e:
            logger.warning(f"RAGAS evaluation failed or timed out: {e}")
            return {
                "faithfulness": None,
                "answer_relevancy": None,
                "evaluation_time_ms": None,
                "error": str(e),
            }
