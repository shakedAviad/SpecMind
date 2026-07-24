from app.evaluation.context_evaluator import ContextEvaluator
from app.graph.state import GraphState


class ContextEvaluationNode:
    def __init__(self, context_evaluator: ContextEvaluator) -> None:
        self._context_evaluator = context_evaluator

    async def __call__(self, state: GraphState) -> dict[str, object]:
        result = await self._context_evaluator.evaluate(
            question=state["resolved_question"],
            chunks=state["reranked_chunks"],
        )

        return {
            "context_is_sufficient": result.is_sufficient,
            "missing_information": result.missing_information,
        }
