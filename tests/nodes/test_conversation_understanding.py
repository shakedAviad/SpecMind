from app.graph.state import GraphState
from app.models.outputs import ConversationUnderstandingResult
from app.nodes.conversation_understanding import ConversationUnderstandingNode


class _FakeConversationUnderstanding:
    def __init__(self, result: ConversationUnderstandingResult) -> None:
        self._result = result
        self.received_question: str | None = None

    async def understand(self, question: str) -> ConversationUnderstandingResult:
        self.received_question = question
        return self._result


async def test_node_invokes_understanding_with_the_original_question() -> None:
    fake = _FakeConversationUnderstanding(ConversationUnderstandingResult(is_follow_up=True))
    node = ConversationUnderstandingNode(understanding=fake)
    state: GraphState = {"session_id": "s1", "original_question": "What about arrays?"}

    await node(state)

    assert fake.received_question == "What about arrays?"


async def test_node_returns_only_the_understanding_fields() -> None:
    fake = _FakeConversationUnderstanding(
        ConversationUnderstandingResult(
            is_follow_up=True,
            missing_context="the earlier topic",
        )
    )
    node = ConversationUnderstandingNode(understanding=fake)
    state: GraphState = {"session_id": "s1", "original_question": "What about arrays?"}

    update = await node(state)

    assert update == {
        "is_follow_up": True,
        "standalone_question": None,
        "missing_context": "the earlier topic",
    }


async def test_node_does_not_mutate_the_input_state() -> None:
    fake = _FakeConversationUnderstanding(ConversationUnderstandingResult(is_follow_up=False))
    node = ConversationUnderstandingNode(understanding=fake)
    state: GraphState = {"session_id": "s1", "original_question": "What is type erasure?"}

    await node(state)

    assert "is_follow_up" not in state
