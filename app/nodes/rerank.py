from app.graph.state import GraphState
from app.reranking.llm_reranker import LlmReranker


class RerankNode:
    def __init__(self, reranker: LlmReranker) -> None:
        self._reranker = reranker

    async def __call__(self, state: GraphState) -> dict[str, object]:
        chunks = await self._reranker.rerank(
            question=state["resolved_question"],
            chunks=state["retrieved_chunks"],
        )

        return {
            "reranked_chunks": chunks,
        }
