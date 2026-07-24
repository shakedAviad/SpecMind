from typing import Any

from app.generation.answer_generator import AnswerGenerator
from app.models.outputs import GeneratedAnswer, ReasoningResult
from app.models.retrieval import RetrievedChunk

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
]

_REASONING = ReasoningResult(
    relevant_points=["Array component types must be reifiable."],
    conclusion="Generic array creation is prohibited.",
    source_chunk_indexes=[0],
)


class _FakeStructuredLlmClient:
    def __init__(self, result: GeneratedAnswer) -> None:
        self._result = result
        self.received_system_prompt: str | None = None
        self.received_user_prompt: str | None = None
        self.received_output_model: type | None = None

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[Any],
    ) -> Any:
        self.received_system_prompt = system_prompt
        self.received_user_prompt = user_prompt
        self.received_output_model = output_model
        return self._result


async def test_generate_returns_the_answer_text() -> None:
    fake_client = _FakeStructuredLlmClient(
        GeneratedAnswer(answer="Generic array creation is prohibited because ...")
    )
    generator = AnswerGenerator(llm_client=fake_client)

    answer = await generator.generate(
        question="Why is generic array creation prohibited?",
        reasoning=_REASONING,
        chunks=_CHUNKS,
    )

    assert answer == "Generic array creation is prohibited because ..."


async def test_generate_builds_a_user_prompt_with_question_reasoning_and_passages() -> None:
    fake_client = _FakeStructuredLlmClient(GeneratedAnswer(answer="answer"))
    generator = AnswerGenerator(llm_client=fake_client)

    await generator.generate(
        question="Why is generic array creation prohibited?",
        reasoning=_REASONING,
        chunks=_CHUNKS,
    )

    assert fake_client.received_user_prompt is not None
    assert "Why is generic array creation prohibited?" in fake_client.received_user_prompt
    assert "Array component types must be reifiable." in fake_client.received_user_prompt
    assert "Generic array creation is prohibited." in fake_client.received_user_prompt
    assert "[0] chunk zero text" in fake_client.received_user_prompt
    assert fake_client.received_output_model is GeneratedAnswer


async def test_generate_handles_empty_reasoning_and_chunks() -> None:
    fake_client = _FakeStructuredLlmClient(GeneratedAnswer(answer="I don't have enough info."))
    generator = AnswerGenerator(llm_client=fake_client)

    empty_reasoning = ReasoningResult(
        relevant_points=[],
        conclusion="The supplied passages do not provide relevant information.",
        source_chunk_indexes=[],
    )

    answer = await generator.generate(
        question="What is a bridge method?",
        reasoning=empty_reasoning,
        chunks=[],
    )

    assert answer == "I don't have enough info."
    assert fake_client.received_user_prompt is not None
    assert "(none)" in fake_client.received_user_prompt
