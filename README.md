# SpecMind

A Python RAG application for answering questions about the Java Language Specification (JLS), built with FastAPI, LangGraph, Qdrant, and BM25 hybrid retrieval.

## Project Status

This project is in early development. The current codebase includes the core Pydantic models, the LangGraph state definition, a structured-output LLM client, environment-based settings, and a session-scoped in-memory store. There is no HTTP API, retrieval pipeline, or Docker setup yet — see [Current Limitations](#current-limitations).

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
* No Docker or Docker Compose setup yet.
* No CI pipeline yet.
* No E2E tests yet.

These will be added incrementally as the corresponding application capabilities are implemented.
