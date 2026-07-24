from typing import Any

from app.evaluation.context_evaluator import ContextEvaluator
from app.models.outputs import ContextEvaluationResult
from app.models.retrieval import RetrievedChunk

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
    RetrievedChunk(chunk_id="jls25-1", document="jls25", chunk_index=1, text="chunk one text"),
]


class _FakeStructuredLlmClient:
    def __init__(self, result: ContextEvaluationResult) -> None:
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


async def test_evaluate_returns_the_llm_result_when_sufficient() -> None:
    fake_client = _FakeStructuredLlmClient(ContextEvaluationResult(is_sufficient=True))
    evaluator = ContextEvaluator(llm_client=fake_client)

    result = await evaluator.evaluate(question="a question", chunks=_CHUNKS)

    assert result.is_sufficient is True
    assert result.missing_information is None


async def test_evaluate_returns_the_llm_result_when_insufficient() -> None:
    fake_client = _FakeStructuredLlmClient(
        ContextEvaluationResult(
            is_sufficient=False,
            missing_information="the specific rule the question asks about",
        )
    )
    evaluator = ContextEvaluator(llm_client=fake_client)

    result = await evaluator.evaluate(question="a question", chunks=_CHUNKS)

    assert result.is_sufficient is False
    assert result.missing_information == "the specific rule the question asks about"


async def test_evaluate_with_no_chunks_is_insufficient_without_calling_the_llm() -> None:
    fake_client = _FakeStructuredLlmClient(ContextEvaluationResult(is_sufficient=True))
    evaluator = ContextEvaluator(llm_client=fake_client)

    result = await evaluator.evaluate(question="a question", chunks=[])

    assert result.is_sufficient is False
    assert result.missing_information is not None
    assert fake_client.call_count == 0


async def test_evaluate_builds_a_user_prompt_with_the_question_and_passages() -> None:
    fake_client = _FakeStructuredLlmClient(ContextEvaluationResult(is_sufficient=True))
    evaluator = ContextEvaluator(llm_client=fake_client)

    await evaluator.evaluate(question="what is type erasure?", chunks=_CHUNKS)

    assert fake_client.received_user_prompt is not None
    assert "what is type erasure?" in fake_client.received_user_prompt
    assert "[0] chunk zero text" in fake_client.received_user_prompt
    assert "[1] chunk one text" in fake_client.received_user_prompt
    assert fake_client.received_output_model is ContextEvaluationResult
