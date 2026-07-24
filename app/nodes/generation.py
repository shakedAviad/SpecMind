from app.generation.answer_generator import AnswerGenerator
from app.graph.state import GraphState


class GenerationNode:
    def __init__(self, answer_generator: AnswerGenerator) -> None:
        self._answer_generator = answer_generator

    async def __call__(self, state: GraphState) -> dict[str, object]:
        answer = await self._answer_generator.generate(
            question=state["resolved_question"],
            reasoning=state["reasoning"],
            chunks=state["reranked_chunks"],
        )

        return {
            "answer": answer,
        }
