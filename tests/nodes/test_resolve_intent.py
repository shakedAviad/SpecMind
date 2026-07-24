from app.graph.state import GraphState
from app.models.outputs import IntentResolution
from app.nodes.resolve_intent import ResolveIntentNode


class _FakeIntentResolver:
    def __init__(self, result: IntentResolution) -> None:
        self._result = result
        self.received_question: str | None = None
        self.received_memory_context: list[str] | None = None

    async def resolve(self, question: str, memory_context: list[str]) -> IntentResolution:
        self.received_question = question
        self.received_memory_context = memory_context
        return self._result


async def test_node_uses_the_standalone_question_when_available() -> None:
    fake = _FakeIntentResolver(
        IntentResolution(resolved_question="What is type erasure?", retrieval_query="q")
    )
    node = ResolveIntentNode(resolver=fake)
    state: GraphState = {
        "original_question": "What is type erasure?",
        "standalone_question": "What is type erasure?",
        "memory_context": [],
    }

    await node(state)

    assert fake.received_question == "What is type erasure?"


async def test_node_falls_back_to_the_original_question_when_no_standalone_question() -> None:
    fake = _FakeIntentResolver(IntentResolution(resolved_question="q", retrieval_query="q"))
    node = ResolveIntentNode(resolver=fake)
    state: GraphState = {
        "original_question": "What about arrays?",
        "memory_context": ["prior fact"],
    }

    await node(state)

    assert fake.received_question == "What about arrays?"
    assert fake.received_memory_context == ["prior fact"]


async def test_node_returns_resolved_question_and_retrieval_query() -> None:
    fake = _FakeIntentResolver(
        IntentResolution(
            resolved_question="Does type erasure also apply to arrays?",
            retrieval_query="type erasure arrays",
        )
    )
    node = ResolveIntentNode(resolver=fake)
    state: GraphState = {"original_question": "What about arrays?", "memory_context": []}

    update = await node(state)

    assert update == {
        "resolved_question": "Does type erasure also apply to arrays?",
        "retrieval_query": "type erasure arrays",
    }
