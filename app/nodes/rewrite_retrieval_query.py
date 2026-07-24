from app.graph.state import GraphState
from app.retrieval.query_rewriter import RetrievalQueryRewriter


class RewriteRetrievalQueryNode:
    def __init__(self, query_rewriter: RetrievalQueryRewriter) -> None:
        self._query_rewriter = query_rewriter

    async def __call__(self, state: GraphState) -> dict[str, object]:
        result = await self._query_rewriter.rewrite(
            question=state["resolved_question"],
            previous_query=state["retrieval_query"],
            missing_information=state.get("missing_information"),
        )

        return {
            "retrieval_query": result.retrieval_query,
            "retry_count": state.get("retry_count", 0) + 1,
        }
