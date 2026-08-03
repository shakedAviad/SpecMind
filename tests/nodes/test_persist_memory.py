from app.graph.state import GraphState
from app.models.outputs import ReasoningResult
from app.nodes.persist_memory import PersistMemoryNode


class _FakeMemoryStore:
    def __init__(self) -> None:
        self.received_session_id: str | None = None
        self.received_facts: list[str] | None = None

    async def add_facts(self, session_id: str, facts: list[str]) -> None:
        self.received_session_id = session_id
        self.received_facts = facts


def _state(**overrides: object) -> GraphState:
    base: GraphState = {
        "session_id": "session-1",
        "resolved_question": "What is type erasure?",
        "reasoning": ReasoningResult(
            relevant_points=["a point"],
            conclusion="a conclusion",
            source_chunk_indexes=[0],
        ),
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


async def test_node_persists_a_fact_derived_from_the_resolved_question_and_conclusion() -> None:
    fake = _FakeMemoryStore()
    node = PersistMemoryNode(memory_store=fake)

    await node(_state())

    assert fake.received_session_id == "session-1"
    assert fake.received_facts == [
        "The user asked: What is type erasure? Conclusion: a conclusion"
    ]


async def test_node_returns_no_state_updates() -> None:
    fake = _FakeMemoryStore()
    node = PersistMemoryNode(memory_store=fake)

    update = await node(_state())

    assert update == {}
