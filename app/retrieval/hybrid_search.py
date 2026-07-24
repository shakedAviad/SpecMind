from itertools import zip_longest

from app.models.retrieval import RetrievedChunk
from app.retrieval.bm25_search import Bm25Search
from app.retrieval.vector_search import VectorSearch


class HybridSearch:
    def __init__(self, vector_search: VectorSearch, bm25_search: Bm25Search) -> None:
        self._vector_search = vector_search
        self._bm25_search = bm25_search

    async def search(self, query: str, limit: int = 10) -> list[RetrievedChunk]:
        vector_results = await self._vector_search.search(query, limit=limit)
        bm25_results = self._bm25_search.search(query, limit=limit)

        return _merge_and_deduplicate(vector_results, bm25_results)


def _merge_and_deduplicate(
    vector_results: list[RetrievedChunk], bm25_results: list[RetrievedChunk]
) -> list[RetrievedChunk]:
    merged: list[RetrievedChunk] = []
    seen_chunk_ids: set[str] = set()

    for vector_chunk, bm25_chunk in zip_longest(vector_results, bm25_results):
        for chunk in (vector_chunk, bm25_chunk):
            if chunk is not None and chunk.chunk_id not in seen_chunk_ids:
                merged.append(chunk)
                seen_chunk_ids.add(chunk.chunk_id)

    return merged
