# SpecMind

A Python RAG application for answering questions about the Java Language Specification (JLS), built with FastAPI, LangGraph, Qdrant, and BM25 hybrid retrieval.

## Project Status

This project is in early development, but the core RAG pipeline is now a fully assembled, working LangGraph graph, wired into a real composition root (`app/container.py`), and exposed over HTTP: `POST /ask` (`app/api/routes.py`) accepts a session ID and question and returns the graph's generated answer, and `GET /health/live` / `GET /health/ready` (`app/api/health.py`) now exist. There is still no persistence of `memory_context` back into `MemoryStore` after a turn, and no Docker setup. See [Current Limitations](#current-limitations) for what remains before this is a deployable system.

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
| `JLS_PDF_PATH` | No | `jls25.pdf` | Path to the JLS PDF used to build the BM25 index at startup |

Loaded via `app/config/settings.py` (`pydantic-settings`). Not required for unit tests, which use deterministic fakes and an in-memory Qdrant client.

## Project Structure

```text
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

* No FastAPI application or HTTP endpoints yet.
* The LLM client (`app/llm/client.py`) is implemented and unit-tested with deterministic fakes but is not yet wired into any graph node.
* The memory store (`app/memory/store.py`) is in-process and session-scoped only; it is not persisted and is not yet wired into any graph node.
* The JLS chunker (`app/chunking/`) is implemented and unit-tested but is not yet wired into any indexing pipeline (no ingestion entry point/script exists yet — `VectorSearch.ingest`/`Bm25Search.index` must currently be called manually).
* Qdrant vector search (`app/retrieval/vector_search.py`) is implemented and tested against an in-memory Qdrant client but is not yet wired into any graph node, and there is no running Qdrant service or Docker setup yet.
* BM25 lexical search (`app/retrieval/bm25_search.py`) is implemented and in-process only (rebuilt from a `list[RetrievedChunk]` in memory); it is not yet wired into any graph node and has no persistence.
* Hybrid search (`app/retrieval/hybrid_search.py`) merges and deduplicates vector and BM25 results by interleaving, without score normalization/fusion (e.g. no RRF); it is not yet wired into any graph node.
* The LLM reranker (`app/reranking/llm_reranker.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient`; it is not yet wired into any graph node.
* Conversation understanding (`app/conversation/understanding.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient`; it is not yet wired into any graph node, and there is no session history for it to consult yet (the memory store exists but isn't connected to it).
* The intent resolver (`app/intent/resolver.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient`; it is not yet wired into any graph node and is not yet connected to the memory store (its `memory_context` must currently be supplied by the caller).
* The context evaluator (`app/evaluation/context_evaluator.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient` (an empty candidate list is judged insufficient without an LLM call); it is not yet wired into any graph node.
* The retrieval query rewriter (`app/retrieval/query_rewriter.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient`; it is not yet wired into any graph node, so the architecture's one-retry-on-insufficient-context loop does not yet exist end-to-end (evaluator → rewriter → re-search → single retry limit are still disconnected pieces).
* The reasoning service (`app/reasoning/service.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient` (an empty candidate list short-circuits to an ungrounded result without an LLM call); it is not yet wired into any graph node.
* The answer generator (`app/generation/answer_generator.py`) is implemented and unit-tested with a deterministic fake `StructuredLlmClient`; it turns a `ReasoningResult` and source passages into the final user-facing `answer` string.
* `app/graph/builder.py` compiles the full pipeline into a working `StateGraph` with the one-retry-on-insufficient-context loop, verified end-to-end with fakes in `tests/graph/test_builder.py` (sufficient on first try, retries once then succeeds, retries once then reasons anyway when still insufficient).
* `app/container.py` now wires real services (not fakes) into that graph — verified in `tests/test_container.py` against an in-memory Qdrant client, but that test still requires the real, untracked `jls25.pdf` (see below). `app/main.py`'s `FastAPI` app builds this container on startup and exposes it via `POST /ask` (`app/api/routes.py`), tested with FastAPI's `TestClient` and a fake graph.
* `GET /health/live` and `GET /health/ready` (`app/api/health.py`) now exist. `/health/ready` currently only checks that `app.state.container` was set during startup (which did call `vector_search.ensure_collection()` against Qdrant once) — it does not re-verify Qdrant/LLM connectivity live on every readiness poll, so a dependency that goes down *after* a successful startup would not be caught. This is good enough to unblock Docker health-check wiring but is a candidate follow-up for the Developer Agent.
* Nothing persists `memory_context` back into `MemoryStore` after a turn completes (the graph reads memory but never writes to it).
* The BM25 index is rebuilt from the full JLS PDF synchronously during container creation (via `load_pdf_pages`/`chunk_pages`), with no separate ingestion step, caching, or progress reporting.
* `tests/chunking/test_jls_integration.py`, `tests/retrieval/test_bm25_search_jls_integration.py`, and now `tests/test_container.py` all require a real `jls25.pdf` placed one directory above the repository root and are not currently skipped when the file is absent — they will fail with a file-not-found error on any machine or CI runner without that file. There is no CI pipeline yet, so this has not surfaced there.
* `mypy` is configured for `python_version = "3.12"` while `pyproject.toml`'s `requires-python` is `>=3.11`; this mismatch should be resolved (either raise `requires-python` or lower the mypy target) before a CI pipeline pins a specific Python version.
* No Docker or Docker Compose setup yet.
* No CI pipeline yet.
* No E2E tests yet.

These will be added incrementally as the corresponding application capabilities are implemented.
