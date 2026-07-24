import re

from rank_bm25 import BM25Okapi

from app.models.retrieval import RetrievedChunk

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class Bm25IndexNotBuiltError(Exception):
    """Raised when search is called before the BM25 index has been built."""


class Bm25Search:
    def __init__(self) -> None:
        self._chunks: list[RetrievedChunk] = []
        self._bm25: BM25Okapi | None = None
        self._indexed = False

    def index(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks
        self._bm25 = BM25Okapi([_tokenize(chunk.text) for chunk in chunks]) if chunks else None
        self._indexed = True

    def search(self, query: str, limit: int = 5) -> list[RetrievedChunk]:
        if not self._indexed:
            raise Bm25IndexNotBuiltError("Bm25Search.index() must be called before search()")

        if self._bm25 is None:
            return []

        scores = self._bm25.get_scores(_tokenize(query))
        ranked_indexes = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        return [
            self._chunks[i].model_copy(update={"score": float(scores[i])})
            for i in ranked_indexes[:limit]
        ]


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())
