from app.graph.state import GraphState
from app.retrieval.hybrid_search import HybridSearch


class RetrieveNode:
    def __init__(self, hybrid_search: HybridSearch) -> None:
        self._hybrid_search = hybrid_search

    async def __call__(self, state: GraphState) -> dict[str, object]:
        chunks = await self._hybrid_search.search(state["retrieval_query"])

        return {
            "retrieved_chunks": chunks,
        }
