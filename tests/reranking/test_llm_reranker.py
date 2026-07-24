from typing import Any

import pytest

from app.models.outputs import RerankResult
from app.models.retrieval import RetrievedChunk
from app.reranking.llm_reranker import LlmReranker, LlmRerankerError

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
    RetrievedChunk(chunk_id="jls25-1", document="jls25", chunk_index=1, text="chunk one text"),
    RetrievedChunk(chunk_id="jls25-2", document="jls25", chunk_index=2, text="chunk two text"),
]


class _FakeStructuredLlmClient:
    def __init__(self, result: RerankResult) -> None:
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


async def test_rerank_returns_chunks_in_llm_reported_order() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[2, 0]))
    reranker = LlmReranker(llm_client=fake_client)

    results = await reranker.rerank(question="a question", chunks=_CHUNKS)

    assert [result.chunk_id for result in results] == ["jls25-2", "jls25-0"]


async def test_rerank_excludes_chunks_not_returned_by_the_llm() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[1]))
    reranker = LlmReranker(llm_client=fake_client)

    results = await reranker.rerank(question="a question", chunks=_CHUNKS)

    assert [result.chunk_id for result in results] == ["jls25-1"]


async def test_rerank_returns_empty_list_when_nothing_is_relevant() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[]))
    reranker = LlmReranker(llm_client=fake_client)

    results = await reranker.rerank(question="a question", chunks=_CHUNKS)

    assert results == []


async def test_rerank_with_no_candidate_chunks_does_not_call_the_llm() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[]))
    reranker = LlmReranker(llm_client=fake_client)

    results = await reranker.rerank(question="a question", chunks=[])

    assert results == []
    assert fake_client.call_count == 0


async def test_rerank_uses_the_rerank_result_model_as_the_output_schema() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[0]))
    reranker = LlmReranker(llm_client=fake_client)

    await reranker.rerank(question="what is type erasure?", chunks=_CHUNKS)

    assert fake_client.received_output_model is RerankResult
    assert fake_client.received_user_prompt is not None
    assert "what is type erasure?" in fake_client.received_user_prompt
    assert "[0] chunk zero text" in fake_client.received_user_prompt
    assert "[2] chunk two text" in fake_client.received_user_prompt


async def test_rerank_raises_on_out_of_range_index() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[5]))
    reranker = LlmReranker(llm_client=fake_client)

    with pytest.raises(LlmRerankerError):
        await reranker.rerank(question="a question", chunks=_CHUNKS)


async def test_rerank_raises_on_duplicate_index() -> None:
    fake_client = _FakeStructuredLlmClient(RerankResult(relevant_chunk_indexes=[0, 0]))
    reranker = LlmReranker(llm_client=fake_client)

    with pytest.raises(LlmRerankerError):
        await reranker.rerank(question="a question", chunks=_CHUNKS)
