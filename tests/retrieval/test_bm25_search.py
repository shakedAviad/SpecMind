import pytest

from app.models.retrieval import RetrievedChunk
from app.retrieval.bm25_search import Bm25IndexNotBuiltError, Bm25Search

_CHUNKS = [
    RetrievedChunk(
        chunk_id="doc-0",
        document="doc",
        chunk_index=0,
        text="Generic types are erased at compile time through type erasure.",
    ),
    RetrievedChunk(
        chunk_id="doc-1",
        document="doc",
        chunk_index=1,
        text="Method overloading resolution depends on the most specific applicable method.",
    ),
    RetrievedChunk(
        chunk_id="doc-2",
        document="doc",
        chunk_index=2,
        text="Arrays are covariant and may raise an array store exception at runtime.",
    ),
]


def test_search_ranks_the_lexically_closest_chunk_first() -> None:
    bm25_search = Bm25Search()
    bm25_search.index(_CHUNKS)

    results = bm25_search.search("type erasure", limit=1)

    assert len(results) == 1
    assert results[0].chunk_id == "doc-0"
    assert results[0].score is not None


def test_search_preserves_chunk_fields() -> None:
    bm25_search = Bm25Search()
    bm25_search.index(_CHUNKS)

    [result] = bm25_search.search("array store exception", limit=1)

    assert result.chunk_id == "doc-2"
    assert result.document == "doc"
    assert result.chunk_index == 2
    assert result.text == _CHUNKS[2].text


def test_search_respects_limit() -> None:
    bm25_search = Bm25Search()
    bm25_search.index(_CHUNKS)

    results = bm25_search.search("method array type", limit=2)

    assert len(results) == 2


def test_search_on_empty_index_returns_no_results() -> None:
    bm25_search = Bm25Search()
    bm25_search.index([])

    results = bm25_search.search("anything", limit=5)

    assert results == []


def test_search_before_index_raises() -> None:
    bm25_search = Bm25Search()

    with pytest.raises(Bm25IndexNotBuiltError):
        bm25_search.search("anything")


def test_reindexing_replaces_the_previous_corpus() -> None:
    bm25_search = Bm25Search()
    bm25_search.index(_CHUNKS)

    bm25_search.index([_CHUNKS[1]])
    results = bm25_search.search("type erasure", limit=5)

    assert [result.chunk_id for result in results] == ["doc-1"]
