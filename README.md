# SpecMind

A Python RAG application for answering questions about the Java Language Specification (JLS), built with FastAPI, LangGraph, Qdrant, and BM25 hybrid retrieval.

## Project Status

This project is in early development. The current codebase includes the core Pydantic models, the LangGraph state definition, a structured-output LLM client, environment-based settings, a session-scoped in-memory store, a JLS PDF loader and chunker, an embedding client, Qdrant-backed vector search, and a BM25 lexical search. There is no HTTP API, hybrid-search fusion of the two retrieval methods, or Docker setup yet — see [Current Limitations](#current-limitations).

## Architecture (Planned)

```text
Question
→ Conversation Understanding
→ Memory Retrieval
→ Resolve Intent
→ Hybrid Search
→ Rerank
→ Context Evaluation
→ Reasoning
→ Generation
```

The workflow uses one retrieval retry when retrieved context is judged insufficient; it does not retry a second time.

## Prerequisites

* Python >= 3.11 (note: `mypy` is currently configured for `python_version = "3.12"`; see [Current Limitations](#current-limitations))
* An OpenAI API key (required to actually invoke the LLM/embedding clients; not required to run the test suite)

## Local Setup

```bash
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate # macOS / Linux

pip install -e ".[dev]"
cp .env.example .env        # macOS / Linux
# copy .env.example .env    # Windows
```

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | API key used by `OpenAiLlmClient` and the embedding client |
| `OPENAI_MODEL` | No | `gpt-4.1-mini` | OpenAI chat model name |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | OpenAI embedding model name |
| `OPENAI_EMBEDDING_DIMENSIONS` | No | `1536` | Must match the vector size produced by `OPENAI_EMBEDDING_MODEL` |
| `QDRANT_URL` | No | `http://localhost:6333` | Qdrant endpoint |
| `QDRANT_COLLECTION_NAME` | No | `jls_chunks` | Qdrant collection used for JLS chunks |

Loaded via `app/config/settings.py` (`pydantic-settings`). Not required for unit tests, which use deterministic fakes and an in-memory Qdrant client.

## Project Structure

```text
app/
  chunking/
    pdf_loader.py      # load_pdf_pages: extracts per-page text from a PDF
    chunker.py         # chunk_pages: splits JLS pages into heading-scoped RetrievedChunks
  config/
    settings.py       # Environment-based Settings (OPENAI_API_KEY, OPENAI_MODEL)
  graph/
    state.py        # LangGraph GraphState and initial-state factory
  llm/
    client.py        # StructuredLlmClient protocol, OpenAiLlmClient, create_chat_model
    embeddings.py     # EmbeddingClient protocol, OpenAiEmbeddingClient, create_embeddings_model
  memory/
    store.py          # MemoryStore: session-scoped, in-memory, isolated per session
  models/
    outputs.py       # ReasoningResult
    retrieval.py      # RetrievedChunk
  retrieval/
    vector_search.py  # VectorSearch: Qdrant collection management, ingest, and search
    bm25_search.py     # Bm25Search: in-memory BM25 lexical search over indexed chunks
tests/
  chunking/
  config/
  graph/
  llm/
  memory/
  models/
  retrieval/
```

## Running Tests

```bash
python -m pytest
```

## Code Quality

```bash
python -m ruff format --check .   # formatting check
python -m ruff format .           # apply formatting
python -m ruff check .            # lint
python -m mypy                    # type check
```

## Current Limitations

* No FastAPI application or HTTP endpoints yet.
* No hybrid-search fusion between vector search and BM25 yet — the two retrieval methods exist independently.
* The LLM client (`app/llm/client.py`) is implemented and unit-tested with deterministic fakes but is not yet wired into any graph node.
* The memory store (`app/memory/store.py`) is in-process and session-scoped only; it is not persisted and is not yet wired into any graph node.
* The JLS chunker (`app/chunking/`) is implemented and unit-tested but is not yet wired into any indexing pipeline (no ingestion entry point/script exists yet — `VectorSearch.ingest`/`Bm25Search.index` must currently be called manually).
* Qdrant vector search (`app/retrieval/vector_search.py`) is implemented and tested against an in-memory Qdrant client but is not yet wired into any graph node, and there is no running Qdrant service or Docker setup yet.
* BM25 lexical search (`app/retrieval/bm25_search.py`) is implemented and in-process only (rebuilt from a `list[RetrievedChunk]` in memory); it is not yet wired into any graph node and has no persistence.
* `tests/chunking/test_jls_integration.py` and `tests/retrieval/test_bm25_search_jls_integration.py` both require a real `jls25.pdf` placed one directory above the repository root and are not currently skipped when the file is absent — they will fail with a file-not-found error on any machine or CI runner without that file. There is no CI pipeline yet, so this has not surfaced there.
* `mypy` is configured for `python_version = "3.12"` while `pyproject.toml`'s `requires-python` is `>=3.11`; this mismatch should be resolved (either raise `requires-python` or lower the mypy target) before a CI pipeline pins a specific Python version.
* No Docker or Docker Compose setup yet.
* No CI pipeline yet.
* No E2E tests yet.

These will be added incrementally as the corresponding application capabilities are implemented.
