"""RAG chain module using LangChain LCEL (LangChain Expression Language)."""

from collections.abc import Iterator
from typing import Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from app.config import get_settings
from app.core.vector_store import VectorStoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# RAG prompt guiding the LLM to answer strictly from retrieved context
RAG_PROMPT_TEMPLATE = """You are a helpful assistant. Answer the question based on the provided context.

If you cannot answer the question based on the context, say "I don't have enough information to answer that question."

Do not make up information. Only use the context provided.

Context:
{context}

Question: {question}

Answer:"""


def format_docs(docs: list[Document]) -> str:
    """Format retrieved Document objects into a single readable context string."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


class RAGChain:
    """End-to-end RAG pipeline for retrieval, answer generation, and evaluation."""

    def __init__(self, vector_store_service: VectorStoreService | None = None):
        """Initialize retriever, prompt, and ChatGroq model."""
        self.vector_store = vector_store_service or VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self._evaluator = None

        # Initialize LLM using Groq (matching requirements.txt and .env)
        self.llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
        )

        self.prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

        # Standard LCEL chain: question -> retrieve context -> prompt -> llm -> parse string
        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        logger.info(f"RAGChain initialized with model='{settings.LLM_MODEL}'")

    @property
    def evaluator(self) -> Any:
        """Lazy-load RAGASEvaluator only when evaluation is requested."""
        if self._evaluator is None:
            from app.core.ragas_evaluator import RAGASEvaluator

            self._evaluator = RAGASEvaluator()
        return self._evaluator

    def query(self, question: str) -> str:
        """Execute a synchronous RAG query and return the answer."""
        logger.info(f"Processing query: '{question[:80]}'...")
        return self.chain.invoke(question)

    def query_with_sources(self, question: str) -> dict:
        """
        Execute RAG query and return both the answer and the source documents.
        Retrieves context once to avoid duplicate vector searches.
        """
        logger.info(f"Processing query with sources: '{question[:80]}'...")
        docs = self.retriever.invoke(question)
        context = format_docs(docs)

        # Generate answer using the retrieved context
        answer = (self.prompt | self.llm | StrOutputParser()).invoke({"context": context, "question": question})

        sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        return {"answer": answer, "sources": sources}

    async def aquery(self, question: str) -> str:
        """Asynchronously execute a RAG query and return the answer."""
        logger.info(f"Processing async query: '{question[:80]}'...")
        return await self.chain.ainvoke(question)

    async def aquery_with_sources(self, question: str) -> dict:
        """
        Asynchronously execute RAG query and return answer with sources.
        Retrieves context once to maximize performance.
        """
        logger.info(f"Processing async query with sources: '{question[:80]}'...")
        docs = await self.retriever.ainvoke(question)
        context = format_docs(docs)

        answer = await (self.prompt | self.llm | StrOutputParser()).ainvoke({"context": context, "question": question})

        sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        return {"answer": answer, "sources": sources}

    async def aquery_with_evaluation(self, question: str) -> dict:
        """Execute async query and evaluate the answer using RAGAS."""
        result = await self.aquery_with_sources(question)
        contexts = [source["content"] for source in result["sources"]]

        try:
            evaluation = await self.evaluator.aevaluate(
                question=question,
                answer=result["answer"],
                contexts=contexts,
            )
            logger.info("RAGAS evaluation completed.")
        except Exception as e:
            logger.warning(f"RAGAS evaluation failed: {e}")
            evaluation = {"error": str(e)}

        result["evaluation"] = evaluation
        return result

    def stream(self, question: str) -> Iterator[str]:
        """Stream response tokens synchronously."""
        logger.info(f"Streaming response for query: '{question[:80]}'...")
        yield from self.chain.stream(question)
