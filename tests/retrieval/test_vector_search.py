from collections.abc import AsyncIterator

import pytest
from qdrant_client import AsyncQdrantClient

from app.models.retrieval import RetrievedChunk
from app.retrieval.vector_search import VectorSearch

_VECTOR_SIZE = 2


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


def _vector_search(
    qdrant_client: AsyncQdrantClient, vectors_by_text: dict[str, list[float]]
) -> VectorSearch:
    return VectorSearch(
        client=qdrant_client,
        embedding_client=_FakeEmbeddingClient(vectors_by_text),
        collection_name="jls_chunks_test",
        vector_size=_VECTOR_SIZE,
    )


async def test_ensure_collection_creates_it_when_missing(
    qdrant_client: AsyncQdrantClient,
) -> None:
    vector_search = _vector_search(qdrant_client, {})

    await vector_search.ensure_collection()

    assert await qdrant_client.collection_exists("jls_chunks_test")


async def test_ensure_collection_is_idempotent(qdrant_client: AsyncQdrantClient) -> None:
    vector_search = _vector_search(qdrant_client, {})

    await vector_search.ensure_collection()
    await vector_search.ensure_collection()

    assert await qdrant_client.collection_exists("jls_chunks_test")


async def test_ingest_then_search_returns_the_closest_chunk_first(
    qdrant_client: AsyncQdrantClient,
) -> None:
    chunks = [
        RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="alpha text"),
        RetrievedChunk(chunk_id="jls25-1", document="jls25", chunk_index=1, text="beta text"),
        RetrievedChunk(chunk_id="jls25-2", document="jls25", chunk_index=2, text="gamma text"),
    ]
    vectors_by_text = {
        "alpha text": [1.0, 0.0],
        "beta text": [0.0, 1.0],
        "gamma text": [0.9, 0.1],
        "query near alpha": [1.0, 0.0],
    }
    vector_search = _vector_search(qdrant_client, vectors_by_text)
    await vector_search.ensure_collection()
    await vector_search.ingest(chunks)

    results = await vector_search.search("query near alpha", limit=2)

    assert [result.chunk_id for result in results] == ["jls25-0", "jls25-2"]
    top_result = results[0]
    assert top_result.document == "jls25"
    assert top_result.chunk_index == 0
    assert top_result.text == "alpha text"
    assert top_result.score is not None


async def test_ingest_upserts_by_chunk_id_instead_of_duplicating(
    qdrant_client: AsyncQdrantClient,
) -> None:
    vectors_by_text = {
        "original text": [1.0, 0.0],
        "updated text": [0.0, 1.0],
        "query near updated": [0.0, 1.0],
    }
    vector_search = _vector_search(qdrant_client, vectors_by_text)
    await vector_search.ensure_collection()

    original = RetrievedChunk(
        chunk_id="jls25-0", document="jls25", chunk_index=0, text="original text"
    )
    await vector_search.ingest([original])

    updated = RetrievedChunk(
        chunk_id="jls25-0", document="jls25", chunk_index=0, text="updated text"
    )
    await vector_search.ingest([updated])

    results = await vector_search.search("query near updated", limit=10)

    assert len(results) == 1
    assert results[0].text == "updated text"


async def test_ingest_with_no_chunks_is_a_no_op(qdrant_client: AsyncQdrantClient) -> None:
    vector_search = _vector_search(qdrant_client, {})

    await vector_search.ingest([])
