from app.graph.state import GraphState
from app.models.outputs import ReasoningResult
from app.models.retrieval import RetrievedChunk
from app.nodes.generation import GenerationNode

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
]
_REASONING = ReasoningResult(
    relevant_points=["a point"], conclusion="a conclusion", source_chunk_indexes=[0]
)


class _FakeAnswerGenerator:
    def __init__(self, answer: str) -> None:
        self._answer = answer
        self.received_question: str | None = None
        self.received_reasoning: ReasoningResult | None = None
        self.received_chunks: list[RetrievedChunk] | None = None

    async def generate(
        self,
        question: str,
        reasoning: ReasoningResult,
        chunks: list[RetrievedChunk],
    ) -> str:
        self.received_question = question
        self.received_reasoning = reasoning
        self.received_chunks = chunks
        return self._answer


async def test_node_invokes_answer_generator_with_question_reasoning_and_chunks() -> None:
    fake = _FakeAnswerGenerator("the final answer")
    node = GenerationNode(answer_generator=fake)
    state: GraphState = {
        "resolved_question": "a question",
        "reasoning": _REASONING,
        "reranked_chunks": _CHUNKS,
    }

    await node(state)

    assert fake.received_question == "a question"
    assert fake.received_reasoning == _REASONING
    assert fake.received_chunks == _CHUNKS


async def test_node_returns_only_the_answer() -> None:
    fake = _FakeAnswerGenerator("the final answer")
    node = GenerationNode(answer_generator=fake)
    state: GraphState = {
        "resolved_question": "a question",
        "reasoning": _REASONING,
        "reranked_chunks": _CHUNKS,
    }

    update = await node(state)

    assert update == {"answer": "the final answer"}
