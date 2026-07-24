from typing import TypedDict

from app.models.outputs import ReasoningResult
from app.models.retrieval import RetrievedChunk


class GraphState(TypedDict, total=False):
    session_id: str

    original_question: str
    resolved_question: str
    retrieval_query: str

    is_follow_up: bool
    standalone_question: str | None
    missing_context: str | None

    memory_context: list[str]

    retrieved_chunks: list[RetrievedChunk]
    reranked_chunks: list[RetrievedChunk]

    context_is_sufficient: bool
    missing_information: str | None
    retry_count: int

    reasoning: ReasoningResult
    answer: str


def create_initial_state(session_id: str, question: str) -> GraphState:
    return GraphState(
        session_id=session_id,
        original_question=question,
        retry_count=0,
    )
