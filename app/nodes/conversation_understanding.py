from app.conversation.understanding import ConversationUnderstanding
from app.graph.state import GraphState


class ConversationUnderstandingNode:
    def __init__(self, understanding: ConversationUnderstanding) -> None:
        self._understanding = understanding

    async def __call__(self, state: GraphState) -> dict[str, object]:
        result = await self._understanding.understand(state["original_question"])

        return {
            "is_follow_up": result.is_follow_up,
            "standalone_question": result.standalone_question,
            "missing_context": result.missing_context,
        }
