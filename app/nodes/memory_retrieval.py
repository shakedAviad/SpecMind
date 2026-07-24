from app.graph.state import GraphState
from app.memory.store import MemoryStore


class MemoryRetrievalNode:
    def __init__(self, memory_store: MemoryStore) -> None:
        self._memory_store = memory_store

    async def __call__(self, state: GraphState) -> dict[str, object]:
        memory_context = await self._memory_store.get_context(state["session_id"])

        return {
            "memory_context": memory_context,
        }
