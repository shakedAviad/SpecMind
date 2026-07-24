from app.graph.state import GraphState
from app.nodes.memory_retrieval import MemoryRetrievalNode


class _FakeMemoryStore:
    def __init__(self, facts: list[str]) -> None:
        self._facts = facts
        self.received_session_id: str | None = None

    async def get_context(self, session_id: str) -> list[str]:
        self.received_session_id = session_id
        return self._facts


async def test_node_invokes_memory_store_with_the_session_id() -> None:
    fake = _FakeMemoryStore(["fact one"])
    node = MemoryRetrievalNode(memory_store=fake)
    state: GraphState = {"session_id": "session-1", "original_question": "q"}

    await node(state)

    assert fake.received_session_id == "session-1"


async def test_node_returns_only_the_memory_context() -> None:
    fake = _FakeMemoryStore(["fact one", "fact two"])
    node = MemoryRetrievalNode(memory_store=fake)
    state: GraphState = {"session_id": "session-1", "original_question": "q"}

    update = await node(state)

    assert update == {"memory_context": ["fact one", "fact two"]}
