from app.graph.state import GraphState
from app.intent.resolver import IntentResolver


class ResolveIntentNode:
    def __init__(self, resolver: IntentResolver) -> None:
        self._resolver = resolver

    async def __call__(self, state: GraphState) -> dict[str, object]:
        question = state.get("standalone_question") or state["original_question"]

        result = await self._resolver.resolve(
            question=question,
            memory_context=state.get("memory_context", []),
        )

        return {
            "resolved_question": result.resolved_question,
            "retrieval_query": result.retrieval_query,
        }
