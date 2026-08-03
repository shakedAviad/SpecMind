from app.graph.state import GraphState
from app.memory.store import MemoryStore


class PersistMemoryNode:
    def __init__(self, memory_store: MemoryStore) -> None:
        self._memory_store = memory_store

    async def __call__(self, state: GraphState) -> dict[str, object]:
        fact = (
            f"The user asked: {state['resolved_question']} "
            f"Conclusion: {state['reasoning'].conclusion}"
        )
        await self._memory_store.add_facts(state["session_id"], [fact])

        return {}
