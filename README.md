# SpecMind

A Python RAG application for answering questions about the Java Language Specification (JLS), built with FastAPI, LangGraph, Qdrant, and BM25 hybrid retrieval.

## Project Status

This project is in early development, but the core RAG pipeline is now a fully assembled, working LangGraph graph, wired into a real composition root (`app/container.py`), and exposed over HTTP: `POST /ask` (`app/api/routes.py`) accepts a session ID and question and returns the graph's generated answer, and `GET /health/live` / `GET /health/ready` (`app/api/health.py`) now exist. The whole stack (app + Qdrant, JLS PDF included) runs with a single `docker compose up --build -d`, and the API can be used directly from a browser via the auto-generated docs at `/docs` — see [Docker](#docker). There is still no persistence of `memory_context` back into `MemoryStore` after a turn. See [Current Limitations](#current-limitations) for what remains before this is a deployable system.

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
* Docker and Docker Compose (only required to run via [Docker](#docker); not required for native local setup or tests)

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
| `JLS_PDF_PATH` | No | `data/jls25.pdf` | Path to the JLS PDF used to build the BM25 index at startup |

Loaded via `app/config/settings.py` (`pydantic-settings`). Not required for unit tests, which use deterministic fakes and an in-memory Qdrant client.

## Docker

Runs the app and Qdrant together via Compose. The JLS PDF (`data/jls25.pdf`) is part of the repository and is built directly into the image, and Qdrant is started and wired up automatically — nothing external to clone or download.

**One-time setup** (only step that can't be automated, since it's a secret):

```bash
cp .env.example .env        # macOS / Linux
# copy .env.example .env    # Windows
```

Then open `.env` and set a real `OPENAI_API_KEY`.

**Single command to run everything:**

```bash
docker compose up --build -d
```

This builds the image (if needed) and starts both `app` and `qdrant`, healthchecked and networked together. Re-running the same command after a code change rebuilds and restarts only what's needed.

```bash
docker compose ps        # both services should report "healthy"
docker compose logs -f app
docker compose down      # stop everything
```

## Talking to the app

Once the stack is up (both services `healthy`), open **`http://localhost:8000/docs`** in a browser — FastAPI's built-in Swagger UI. Expand `POST /ask`, click "Try it out", fill in just a `question` (`session_id` is optional — omit it to start a new session; the server generates one and returns it in the response for follow-up calls), and click "Execute" to get a real answer, no `curl` required. `http://localhost:8000/redoc` gives a read-only alternative view of the same API.

Other endpoints, once the stack is up:

* `GET http://localhost:8000/health/live` — liveness
* `GET http://localhost:8000/health/ready` — readiness (503 until the container/graph finished building at startup)
* `POST http://localhost:8000/ask` — `{"question": "...", "session_id": "..."}` (`session_id` optional — auto-generated and echoed back if omitted; requires a real `OPENAI_API_KEY` in `.env` to actually produce an answer)
* Qdrant is also reachable directly at `http://localhost:6333`

## Project Structure

```text
Dockerfile
.dockerignore
compose.yaml
data/
  jls25.pdf          # Java Language Specification PDF, used to build the BM25 index at startup
app/
  main.py            # FastAPI app; builds the AppContainer on startup via lifespan
  container.py        # create_app_container: composition root wiring real services into build_graph
  api/
    routes.py          # POST /ask: invokes the graph and returns the generated answer
    health.py          # GET /health/live, GET /health/ready
  conversation/
    understanding.py   # ConversationUnderstanding: LLM-based follow-up detection
  chunking/
    pdf_loader.py      # load_pdf_pages: extracts per-page text from a PDF
    chunker.py         # chunk_pages: splits JLS pages into heading-scoped RetrievedChunks
  intent/
    resolver.py        # IntentResolver: LLM-based question resolution + retrieval query
  evaluation/
    context_evaluator.py  # ContextEvaluator: LLM-based sufficiency judgment over retrieved passages
  reasoning/
    service.py         # ReasoningService: LLM-based grounded reasoning over retrieved passages
  generation/
    answer_generator.py  # AnswerGenerator: LLM-based final natural-language answer
  config/
    settings.py       # Environment-based Settings (OPENAI_API_KEY, OPENAI_MODEL)
  graph/
    state.py        # LangGraph GraphState and initial-state factory
    builder.py       # build_graph: compiles the full StateGraph with the one-retry loop
  nodes/
    conversation_understanding.py  # ConversationUnderstandingNode
    memory_retrieval.py             # MemoryRetrievalNode
    resolve_intent.py               # ResolveIntentNode
    retrieve.py                     # RetrieveNode (hybrid search)
    rerank.py                       # RerankNode
    context_evaluation.py           # ContextEvaluationNode
    rewrite_retrieval_query.py      # RewriteRetrievalQueryNode
    reasoning.py                    # ReasoningNode
    generation.py                   # GenerationNode
  llm/
    client.py        # StructuredLlmClient protocol, OpenAiLlmClient, create_chat_model
    embeddings.py     # EmbeddingClient protocol, OpenAiEmbeddingClient, create_embeddings_model
  memory/
    store.py          # MemoryStore: session-scoped, in-memory, isolated per session
  models/
    outputs.py       # ReasoningResult, RerankResult, ConversationUnderstandingResult, IntentResolution, ContextEvaluationResult, QueryRewriteResult, GeneratedAnswer
    retrieval.py      # RetrievedChunk
    api.py            # AskRequest, AskResponse, HealthStatus
  reranking/
    llm_reranker.py    # LlmReranker: LLM-based relevance reranking of candidate chunks
  retrieval/
    vector_search.py  # VectorSearch: Qdrant collection management, ingest, and search
    bm25_search.py     # Bm25Search: in-memory BM25 lexical search over indexed chunks
    hybrid_search.py   # HybridSearch: merges and deduplicates vector + BM25 results
    query_rewriter.py  # RetrievalQueryRewriter: LLM-based query revision for the one-retry step
tests/
  api/
  chunking/
  config/
  conversation/
  evaluation/
  generation/
  graph/
  intent/
  llm/
  memory/
  models/
  nodes/
  reasoning/
  reranking/
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

* The LLM client, memory store, chunker, vector search, BM25 search, hybrid search, reranker, conversation understanding, intent resolver, context evaluator, query rewriter, reasoning service, and answer generator are each implemented and unit-tested (many with deterministic fakes), and are all wired together by `app/graph/builder.py` into a working `StateGraph` with the one-retry-on-insufficient-context loop — verified end-to-end with fakes in `tests/graph/test_builder.py` (sufficient on first try, retries once then succeeds, retries once then reasons anyway when still insufficient).
* `app/container.py` wires real services (not fakes) into that graph, exposed over HTTP via `POST /ask`. Verified by actually running the Dockerized stack and asking a real question end-to-end (real Qdrant, real OpenAI calls, real JLS PDF) — not just the in-memory client used in `tests/test_container.py`.
* `GET /health/ready` (`app/api/health.py`) currently only checks that `app.state.container` was set during startup (which did call `vector_search.ensure_collection()` against Qdrant once) — it does not re-verify Qdrant/LLM connectivity live on every readiness poll, so a dependency that goes down *after* a successful startup would not be caught. Good enough for Docker health-check wiring today, but a candidate follow-up for a live check.
* Nothing persists `memory_context` back into `MemoryStore` after a turn completes (the graph reads memory but never writes to it), and `MemoryStore` itself is in-process only — it does not survive an app restart, and does not currently run as a separate service, so it cannot be shared across multiple app replicas.
* The BM25 index is rebuilt from the full JLS PDF synchronously during container/app startup (via `load_pdf_pages`/`chunk_pages`), with no separate ingestion step, caching, or progress reporting — every restart re-parses and re-chunks the entire PDF.
* `mypy` is configured for `python_version = "3.12"` while `pyproject.toml`'s `requires-python` is `>=3.11`; this mismatch should be resolved (either raise `requires-python` or lower the mypy target) before pinning a specific Python version elsewhere.

These will be added incrementally as the corresponding application capabilities are implemented.
