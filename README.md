# 🚀 InsightFlow: Enterprise Document Intelligence & RAG Platform

**InsightFlow** is a production-ready, asynchronous **Retrieval-Augmented Generation (RAG)** platform built with **FastAPI**, **LangChain (LCEL)**, **Qdrant Vector Database**, **Groq LLM**, **Google Gemini Embeddings**, and **RAGAS** automated answer evaluation.

---

## 📑 Table of Contents
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Structure](#-project-structure)
- [Key Features](#-key-features)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
- [Running the Application](#-running-the-application)
- [API Reference & Usage](#-api-reference--usage)
  - [1. Health & Readiness](#1-health--readiness)
  - [2. Document Ingestion](#2-document-ingestion)
  - [3. Asking Questions (RAG Query)](#3-asking-questions-rag-query)
  - [4. Streaming Responses](#4-streaming-responses)
  - [5. Similarity Search](#5-similarity-search)
- [RAGAS Evaluation](#-ragas-evaluation)
- [Observability with LangSmith](#-observability-with-langsmith)

---

## 🏗️ Architecture & Tech Stack

```
[ User Request ]
       │
       ▼
 [ FastAPI API ] ─── (Uploads: PDF / TXT / CSV) ───► [ DocumentProcessor ]
       │                                                     │
       │                                          (Chunks & Metadata)
       │                                                     │
       ▼                                                     ▼
 [ LangChain LCEL ] ◄── (Embeddings: 768-dim) ──► [ Google Gemini Embeddings ]
       │                                                     │
       ├────────────────► [ Qdrant Vector DB ] ◄─────────────┘
       │                 (Cosine Similarity)
       ▼
   [ Groq LLM ] ───► (Streaming / Static Answers)
       │
       ▼
 [ RAGAS Evaluation ] ───► (Faithfulness & Answer Relevancy Scores)
```

- **Framework:** FastAPI (Asynchronous REST API)
- **Vector Database:** Qdrant Cloud
- **LLM Provider:** Groq (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)
- **Embeddings:** Google Gemini (`models/text-embedding-004`, 768 dimensions)
- **Orchestration:** LangChain LCEL (LangChain Expression Language)
- **Evaluation:** RAGAS (Reference-free faithfulness and answer relevance)
- **Config & Validation:** Pydantic V2 & Pydantic-Settings

---

## 📂 Project Structure

```text
rag-project/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── documents.py   # Upload, inspect, and delete collections
│   │   │   ├── health.py      # Liveness and Qdrant readiness probes
│   │   │   └── query.py       # RAG query, streaming, and similarity search
│   │   └── schemas.py         # Pydantic request and response models
│   ├── core/
│   │   ├── document_processor.py  # Text loading & chunking (PDF, TXT, CSV)
│   │   ├── embeddings.py          # Google Gemini embedding service
│   │   ├── rag_chain.py           # LangChain LCEL question-answering pipeline
│   │   ├── ragas_evaluator.py     # RAGAS metrics evaluation service
│   │   └── vector_store.py        # Qdrant client & indexing operations
│   ├── utils/
│   │   └── logger.py          # Centralized application logging
│   ├── config.py              # Pydantic-settings environment configuration
│   └── main.py                # FastAPI application entry point
├── .env                       # Environment secrets (API keys & endpoints)
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── template.py                # Lightweight project structure generator
└── README.md                  # Project documentation
```

---

## ✨ Key Features

- **Multi-Format Ingestion:** Seamlessly upload and chunk `.pdf`, `.txt`, and `.csv` files.
- **Single-Pass Retrieval:** Eliminates redundant vector queries, halving latency when returning source citations.
- **Real-Time Token Streaming:** Stream answers token-by-token using `StreamingResponse`.
- **Integrated RAGAS Evaluation:** Optional, on-the-fly calculation of **Faithfulness** and **Answer Relevancy** scores.
- **Dynamic Vector Resizing:** Configured with 768-dimensional vectors matching Google's `text-embedding-004`.
- **Case-Insensitive Settings:** Robust Pydantic V2 configuration loaded from `.env`.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- A [Groq Cloud API Key](https://console.groq.com)
- A [Google AI Studio API Key](https://aistudio.google.com)
- A [Qdrant Cloud Cluster](https://cloud.qdrant.io)

### Installation

1. **Clone the repository and navigate into the project:**
   ```bash
   cd rag-project
   ```

2. **Create and activate a virtual environment:**
   - **Linux / macOS:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration

Create or update your `.env` file in the project root:

```env
# ===========================================
# LLM & Embedding Providers
# ===========================================
GROQ_API_KEY=gsk_your_groq_api_key_here
GOOGLE_API_KEY=AIzaSy_your_google_api_key_here

# ===========================================
# Qdrant Cloud Configuration
# ===========================================
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
COLLECTION_NAME=rag_documents

# ===========================================
# Model & Chunking Configuration
# ===========================================
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=models/text-embedding-004
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.0
RETRIEVAL_K=4

# ===========================================
# Optional: LangSmith Tracing
# ===========================================
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_your_langsmith_key_here
LANGCHAIN_PROJECT=insightflow-production
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

---

## 🏃 Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running, interactive API documentation is available at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Reference & Usage

### 1. Health & Readiness

#### Check Service Liveness
```bash
curl -X GET "http://localhost:8000/health"
```
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-11-21T17:45:00Z"
}
```

#### Check Qdrant Readiness
```bash
curl -X GET "http://localhost:8000/health/ready"
```

---

### 2. Document Ingestion

#### Upload and Ingest a File (PDF, TXT, CSV)
```bash
curl -X POST "http://localhost:8000/documents/upload" \
     -F "file=@sample_notes.pdf"
```
```json
{
  "message": "Document uploaded and processed successfully",
  "filename": "sample_notes.pdf",
  "chunks_created": 14,
  "document_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6", "..."]
}
```

#### Get Collection Point Statistics
```bash
curl -X GET "http://localhost:8000/documents/info"
```

#### Delete Entire Collection
```bash
curl -X DELETE "http://localhost:8000/documents/collection"
```

---

### 3. Asking Questions (RAG Query)

#### Basic Query with Citations
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What are the key findings mentioned in the document?",
       "include_sources": true,
       "enable_evaluation": false
     }'
```
```json
{
  "question": "What are the key findings mentioned in the document?",
  "answer": "Based on the provided context, the key findings include...",
  "sources": [
    {
      "content": "Excerpt text from the indexed document chunk...",
      "metadata": {
        "source": "sample_notes.pdf",
        "page": 1
      }
    }
  ],
  "processing_time_ms": 684.21,
  "evaluation": null
}
```

---

### 4. Streaming Responses

Receive tokens as they are generated by the LLM:

```bash
curl -X POST "http://localhost:8000/query/stream" \
     -H "Content-Type: application/json" \
     -d '{"question": "Summarize the project goals in 3 bullet points."}'
```

---

### 5. Similarity Search

Inspect retrieved chunks and cosine distance scores without triggering LLM generation:

```bash
curl -X POST "http://localhost:8000/query/search" \
     -H "Content-Type: application/json" \
     -d '{"question": "Machine learning architectures"}'
```

---

## 📊 RAGAS Evaluation

When `"enable_evaluation": true` is passed to `POST /query`, the system evaluates the generated answer against the retrieved context:

- **Faithfulness (0.0 to 1.0):** Measures whether the answer is strictly derived from the context (preventing hallucinations).
- **Answer Relevancy (0.0 to 1.0):** Measures how directly and completely the answer addresses the user's prompt.

```json
{
  "evaluation": {
    "faithfulness": 0.9500,
    "answer_relevancy": 0.9231,
    "evaluation_time_ms": 1240.50,
    "error": null
  }
}
```

---

## 🔭 Observability with LangSmith

If `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` are provided in `.env`, LangChain automatically traces every retrieval, prompt rendering, and LLM call in real-time. You can monitor latency, token usage, and execution graphs directly on [smith.langchain.com](https://smith.langchain.com).
