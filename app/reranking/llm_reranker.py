from app.llm.client import StructuredLlmClient
from app.models.outputs import RerankResult
from app.models.retrieval import RetrievedChunk


class LlmRerankerError(Exception):
    """Raised when the reranker's structured output references invalid candidate indexes."""


class LlmReranker:
    _SYSTEM_PROMPT = (
        "You are reranking candidate passages from the Java Language Specification "
        "for relevance to a user's question.\n\n"
        "Given the question and a numbered list of candidate passages, return the "
        "indexes of the passages that are relevant to answering the question, "
        "ordered from most to least relevant. Exclude passages that are not "
        "relevant. If none are relevant, return an empty list.\n\n"
        "Each passage is prefixed with its index in square brackets, for example "
        "'[0] ...'. Indexes are zero-based; the returned indexes must match those "
        "bracketed numbers exactly.\n\n"
        "Example: given passages [0], [1], [2], [3], [4] where only [1] and [4] are "
        "relevant and [4] is the more relevant of the two, return [4, 1]."
    )

    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []

        result = await self._llm_client.generate_structured(
            system_prompt=self._SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(question, chunks),
            output_model=RerankResult,
        )

        return _resolve_chunks(result, chunks)


def _build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    candidates = "\n\n".join(f"[{index}] {chunk.text}" for index, chunk in enumerate(chunks))
    return f"Question: {question}\n\nCandidate passages:\n{candidates}"


def _resolve_chunks(result: RerankResult, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    resolved: list[RetrievedChunk] = []
    seen_indexes: set[int] = set()

    for index in result.relevant_chunk_indexes:
        if index < 0 or index >= len(chunks):
            raise LlmRerankerError(
                f"LLM returned out-of-range candidate index {index} for {len(chunks)} chunks"
            )
        if index in seen_indexes:
            raise LlmRerankerError(f"LLM returned duplicate candidate index {index}")

        seen_indexes.add(index)
        resolved.append(chunks[index])

    return resolved
