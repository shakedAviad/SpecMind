from app.graph.state import GraphState
from app.reasoning.service import ReasoningService


class ReasoningNode:
    def __init__(self, reasoning_service: ReasoningService) -> None:
        self._reasoning_service = reasoning_service

    async def __call__(self, state: GraphState) -> dict[str, object]:
        result = await self._reasoning_service.reason(
            question=state["resolved_question"],
            chunks=state["reranked_chunks"],
        )

        return {
            "reasoning": result,
        }
