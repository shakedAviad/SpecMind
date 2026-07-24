from collections.abc import AsyncIterator

import pytest
from qdrant_client import AsyncQdrantClient

from app.models.retrieval import RetrievedChunk
from app.retrieval.bm25_search import Bm25Search
from app.retrieval.hybrid_search import HybridSearch
from app.retrieval.vector_search import VectorSearch

_VECTOR_SIZE = 2

_CHUNKS = [
    RetrievedChunk(
        chunk_id="jls25-0", document="jls25", chunk_index=0, text="alpha lexical match query terms"
    ),
    RetrievedChunk(
        chunk_id="jls25-1", document="jls25", chunk_index=1, text="totally unrelated filler content"
    ),
    RetrievedChunk(
        chunk_id="jls25-2",
        document="jls25",
        chunk_index=2,
        text="query terms lexical match again repeated words",
    ),
    RetrievedChunk(
        chunk_id="jls25-3",
        document="jls25",
        chunk_index=3,
        text="something else entirely different filler",
    ),
    RetrievedChunk(
        chunk_id="jls25-4", document="jls25", chunk_index=4, text="beta gamma delta epsilon zeta"
    ),
    RetrievedChunk(
        chunk_id="jls25-5", document="jls25", chunk_index=5, text="eta theta iota kappa lambda"
    ),
]

# Vectors chosen so cosine similarity to the query vector [1.0, 0.0] ranks
# jls25-0 and jls25-1 highest; BM25 lexical overlap ranks jls25-0 and jls25-2 highest.
_VECTORS_BY_TEXT = {
    "alpha lexical match query terms": [1.0, 0.0],
    "totally unrelated filler content": [0.99, 0.01],
    "query terms lexical match again repeated words": [0.0, 1.0],
    "something else entirely different filler": [-1.0, 0.0],
    "beta gamma delta epsilon zeta": [0.0, -1.0],
    "eta theta iota kappa lambda": [-0.5, -0.5],
    "hybrid query": [1.0, 0.0],
}


class _FakeEmbeddingClient:
    def __init__(self, vectors_by_text: dict[str, list[float]]) -> None:
        self._vectors_by_text = vectors_by_text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors_by_text[text] for text in texts]


@pytest.fixture
async def qdrant_client() -> AsyncIterator[AsyncQdrantClient]:
    client = AsyncQdrantClient(location=":memory:")
    try:
        yield client
    finally:
        await client.close()


async def _build_hybrid_search(qdrant_client: AsyncQdrantClient) -> HybridSearch:
    vector_search = VectorSearch(
        client=qdrant_client,
        embedding_client=_FakeEmbeddingClient(_VECTORS_BY_TEXT),
        collection_name="jls_chunks_test",
        vector_size=_VECTOR_SIZE,
    )
    await vector_search.ensure_collection()
    await vector_search.ingest(_CHUNKS)

    bm25_search = Bm25Search()
    bm25_search.index(_CHUNKS)

    return HybridSearch(vector_search=vector_search, bm25_search=bm25_search)


async def test_search_merges_and_deduplicates_vector_and_bm25_candidates(
    qdrant_client: AsyncQdrantClient,
) -> None:
    hybrid_search = await _build_hybrid_search(qdrant_client)

    results = await hybrid_search.search("hybrid query", limit=2)

    assert [result.chunk_id for result in results] == ["jls25-0", "jls25-1", "jls25-2"]


async def test_search_does_not_duplicate_a_chunk_found_by_both_sources(
    qdrant_client: AsyncQdrantClient,
) -> None:
    hybrid_search = await _build_hybrid_search(qdrant_client)

    results = await hybrid_search.search("hybrid query", limit=2)

    chunk_ids = [result.chunk_id for result in results]
    assert chunk_ids.count("jls25-0") == 1
