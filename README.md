# SpecMind

A Python RAG application for answering questions about the Java Language Specification (JLS), built with FastAPI, LangGraph, Qdrant, and BM25 hybrid retrieval.

## Project Status

This project is in early development. The current codebase includes only the core Pydantic models and the LangGraph state definition. There is no HTTP API, retrieval pipeline, or Docker setup yet — see [Current Limitations](#current-limitations).

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

## Local Setup

```bash
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate # macOS / Linux

pip install -e ".[dev]"
```

## Project Structure

```text
app/
  graph/
    state.py        # LangGraph GraphState and initial-state factory
  models/
    outputs.py       # ReasoningResult
    retrieval.py      # RetrievedChunk
tests/
  graph/
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
* No Docker or Docker Compose setup yet.
* No CI pipeline yet.
* No E2E tests yet.

These will be added incrementally as the corresponding application capabilities are implemented.
