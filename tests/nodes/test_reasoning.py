from app.graph.state import GraphState
from app.models.outputs import ReasoningResult
from app.models.retrieval import RetrievedChunk
from app.nodes.reasoning import ReasoningNode

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
]


class _FakeReasoningService:
    def __init__(self, result: ReasoningResult) -> None:
        self._result = result
        self.received_question: str | None = None
        self.received_chunks: list[RetrievedChunk] | None = None

    async def reason(self, question: str, chunks: list[RetrievedChunk]) -> ReasoningResult:
        self.received_question = question
        self.received_chunks = chunks
        return self._result


async def test_node_invokes_reasoning_service_with_resolved_question_and_reranked_chunks() -> None:
    expected = ReasoningResult(relevant_points=[], conclusion="c", source_chunk_indexes=[])
    fake = _FakeReasoningService(expected)
    node = ReasoningNode(reasoning_service=fake)
    state: GraphState = {"resolved_question": "a question", "reranked_chunks": _CHUNKS}

    await node(state)

    assert fake.received_question == "a question"
    assert fake.received_chunks == _CHUNKS


async def test_node_returns_only_the_reasoning_result() -> None:
    expected = ReasoningResult(
        relevant_points=["a point"], conclusion="a conclusion", source_chunk_indexes=[0]
    )
    fake = _FakeReasoningService(expected)
    node = ReasoningNode(reasoning_service=fake)
    state: GraphState = {"resolved_question": "a question", "reranked_chunks": _CHUNKS}

    update = await node(state)

    assert update == {"reasoning": expected}
