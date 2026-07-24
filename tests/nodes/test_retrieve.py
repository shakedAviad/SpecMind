from app.graph.state import GraphState
from app.models.retrieval import RetrievedChunk
from app.nodes.retrieve import RetrieveNode

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
]


class _FakeHybridSearch:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks
        self.received_query: str | None = None

    async def search(self, query: str) -> list[RetrievedChunk]:
        self.received_query = query
        return self._chunks


async def test_node_invokes_hybrid_search_with_the_retrieval_query() -> None:
    fake = _FakeHybridSearch(_CHUNKS)
    node = RetrieveNode(hybrid_search=fake)
    state: GraphState = {"retrieval_query": "type erasure arrays"}

    await node(state)

    assert fake.received_query == "type erasure arrays"


async def test_node_returns_only_the_retrieved_chunks() -> None:
    fake = _FakeHybridSearch(_CHUNKS)
    node = RetrieveNode(hybrid_search=fake)
    state: GraphState = {"retrieval_query": "type erasure arrays"}

    update = await node(state)

    assert update == {"retrieved_chunks": _CHUNKS}
