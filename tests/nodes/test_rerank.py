from app.graph.state import GraphState
from app.models.retrieval import RetrievedChunk
from app.nodes.rerank import RerankNode

_RETRIEVED = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
    RetrievedChunk(chunk_id="jls25-1", document="jls25", chunk_index=1, text="chunk one text"),
]
_RERANKED = [_RETRIEVED[1]]


class _FakeLlmReranker:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks
        self.received_question: str | None = None
        self.received_chunks: list[RetrievedChunk] | None = None

    async def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        self.received_question = question
        self.received_chunks = chunks
        return self._chunks


async def test_node_invokes_reranker_with_resolved_question_and_retrieved_chunks() -> None:
    fake = _FakeLlmReranker(_RERANKED)
    node = RerankNode(reranker=fake)
    state: GraphState = {
        "resolved_question": "Does type erasure also apply to arrays?",
        "retrieved_chunks": _RETRIEVED,
    }

    await node(state)

    assert fake.received_question == "Does type erasure also apply to arrays?"
    assert fake.received_chunks == _RETRIEVED


async def test_node_returns_only_the_reranked_chunks() -> None:
    fake = _FakeLlmReranker(_RERANKED)
    node = RerankNode(reranker=fake)
    state: GraphState = {
        "resolved_question": "a question",
        "retrieved_chunks": _RETRIEVED,
    }

    update = await node(state)

    assert update == {"reranked_chunks": _RERANKED}
