# SpecMind

A Python RAG application for answering questions about the Java Language Specification (JLS), built with FastAPI, LangGraph, Qdrant, and BM25 hybrid retrieval.

## Project Status

This project is in early development. The current codebase includes the core Pydantic models, the LangGraph state definition, a structured-output LLM client, environment-based settings, a session-scoped in-memory store, and a JLS PDF loader and chunker. There is no HTTP API, retrieval pipeline (Qdrant/BM25), or Docker setup yet — see [Current Limitations](#current-limitations).

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

* Python >= 3.11
* An OpenAI API key (required to actually invoke the LLM client; not required to run the test suite)

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
| `OPENAI_API_KEY` | Yes | — | API key used by `OpenAiLlmClient` |
| `OPENAI_MODEL` | No | `gpt-4.1-mini` | OpenAI model name |

Loaded via `app/config/settings.py` (`pydantic-settings`). Not required for unit tests, which use deterministic fakes.

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
  memory/
    store.py          # MemoryStore: session-scoped, in-memory, isolated per session
  models/
    outputs.py       # ReasoningResult
    retrieval.py      # RetrievedChunk
tests/
  chunking/
  config/
  graph/
  llm/
  memory/
  models/
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
* No Qdrant or BM25 retrieval integration yet.
* The LLM client (`app/llm/client.py`) is implemented and unit-tested with deterministic fakes but is not yet wired into any graph node.
* The memory store (`app/memory/store.py`) is in-process and session-scoped only; it is not persisted and is not yet wired into any graph node.
* The JLS chunker (`app/chunking/`) is implemented and unit-tested but is not yet wired into any indexing pipeline (no Qdrant/BM25 index yet).
* `tests/chunking/test_jls_integration.py` requires a real `jls25.pdf` placed one directory above the repository root and is not currently skipped when the file is absent — it will fail with a file-not-found error on any machine or CI runner without that file. There is no CI pipeline yet, so this has not surfaced there.
* No Docker or Docker Compose setup yet.
* No CI pipeline yet.
* No E2E tests yet.

These will be added incrementally as the corresponding application capabilities are implemented.
