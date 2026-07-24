from typing import Any

from app.models.outputs import ReasoningResult
from app.models.retrieval import RetrievedChunk
from app.reasoning.service import ReasoningService

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
    RetrievedChunk(chunk_id="jls25-1", document="jls25", chunk_index=1, text="chunk one text"),
]


class _FakeStructuredLlmClient:
    def __init__(self, result: ReasoningResult) -> None:
        self._result = result
        self.received_system_prompt: str | None = None
        self.received_user_prompt: str | None = None
        self.received_output_model: type | None = None
        self.call_count = 0

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[Any],
    ) -> Any:
        self.call_count += 1
        self.received_system_prompt = system_prompt
        self.received_user_prompt = user_prompt
        self.received_output_model = output_model
        return self._result


async def test_reason_returns_the_llm_result() -> None:
    expected = ReasoningResult(
        relevant_points=["Arrays require a reifiable component type."],
        conclusion="Generic array creation is prohibited.",
        source_chunk_indexes=[0],
    )
    fake_client = _FakeStructuredLlmClient(expected)
    service = ReasoningService(llm_client=fake_client)

    result = await service.reason(question="a question", chunks=_CHUNKS)

    assert result == expected


async def test_reason_with_no_chunks_returns_ungrounded_result_without_calling_the_llm() -> None:
    fake_client = _FakeStructuredLlmClient(
        ReasoningResult(relevant_points=[], conclusion="unused", source_chunk_indexes=[])
    )
    service = ReasoningService(llm_client=fake_client)

    result = await service.reason(question="a question", chunks=[])

    assert result.relevant_points == []
    assert result.source_chunk_indexes == []
    assert result.conclusion
    assert fake_client.call_count == 0


async def test_reason_builds_a_user_prompt_with_the_question_and_passages() -> None:
    fake_client = _FakeStructuredLlmClient(
        ReasoningResult(relevant_points=[], conclusion="c", source_chunk_indexes=[])
    )
    service = ReasoningService(llm_client=fake_client)

    await service.reason(question="what is type erasure?", chunks=_CHUNKS)

    assert fake_client.received_user_prompt is not None
    assert "what is type erasure?" in fake_client.received_user_prompt
    assert "[0] chunk zero text" in fake_client.received_user_prompt
    assert "[1] chunk one text" in fake_client.received_user_prompt
    assert fake_client.received_output_model is ReasoningResult
