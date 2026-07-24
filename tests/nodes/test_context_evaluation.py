from app.graph.state import GraphState
from app.models.outputs import ContextEvaluationResult
from app.models.retrieval import RetrievedChunk
from app.nodes.context_evaluation import ContextEvaluationNode

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
]


class _FakeContextEvaluator:
    def __init__(self, result: ContextEvaluationResult) -> None:
        self._result = result
        self.received_question: str | None = None
        self.received_chunks: list[RetrievedChunk] | None = None

    async def evaluate(
        self, question: str, chunks: list[RetrievedChunk]
    ) -> ContextEvaluationResult:
        self.received_question = question
        self.received_chunks = chunks
        return self._result


async def test_node_invokes_evaluator_with_resolved_question_and_reranked_chunks() -> None:
    fake = _FakeContextEvaluator(ContextEvaluationResult(is_sufficient=True))
    node = ContextEvaluationNode(context_evaluator=fake)
    state: GraphState = {"resolved_question": "a question", "reranked_chunks": _CHUNKS}

    await node(state)

    assert fake.received_question == "a question"
    assert fake.received_chunks == _CHUNKS


async def test_node_returns_sufficiency_and_missing_information() -> None:
    fake = _FakeContextEvaluator(
        ContextEvaluationResult(is_sufficient=False, missing_information="the missing rule")
    )
    node = ContextEvaluationNode(context_evaluator=fake)
    state: GraphState = {"resolved_question": "a question", "reranked_chunks": _CHUNKS}

    update = await node(state)

    assert update == {
        "context_is_sufficient": False,
        "missing_information": "the missing rule",
    }
