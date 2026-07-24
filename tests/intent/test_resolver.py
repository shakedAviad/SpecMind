from typing import Any

from app.intent.resolver import IntentResolver
from app.models.outputs import IntentResolution


class _FakeStructuredLlmClient:
    def __init__(self, result: IntentResolution) -> None:
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


async def test_resolve_returns_the_llm_result() -> None:
    fake_client = _FakeStructuredLlmClient(
        IntentResolution(
            resolved_question="Does type erasure also apply to arrays?",
            retrieval_query="type erasure arrays",
        )
    )
    resolver = IntentResolver(llm_client=fake_client)

    result = await resolver.resolve(question="What about arrays?", memory_context=[])

    assert result.resolved_question == "Does type erasure also apply to arrays?"
    assert result.retrieval_query == "type erasure arrays"


async def test_resolve_includes_memory_facts_in_the_user_prompt() -> None:
    fake_client = _FakeStructuredLlmClient(
        IntentResolution(resolved_question="q", retrieval_query="q")
    )
    resolver = IntentResolver(llm_client=fake_client)

    await resolver.resolve(
        question="What about arrays?",
        memory_context=["The user previously asked about generic type erasure."],
    )

    assert fake_client.received_user_prompt is not None
    assert "What about arrays?" in fake_client.received_user_prompt
    assert "The user previously asked about generic type erasure." in (
        fake_client.received_user_prompt
    )


async def test_resolve_marks_absent_memory_explicitly() -> None:
    fake_client = _FakeStructuredLlmClient(
        IntentResolution(resolved_question="q", retrieval_query="q")
    )
    resolver = IntentResolver(llm_client=fake_client)

    await resolver.resolve(question="What is type erasure?", memory_context=[])

    assert fake_client.received_user_prompt is not None
    assert "(none)" in fake_client.received_user_prompt


async def test_resolve_uses_the_intent_resolution_model_as_the_output_schema() -> None:
    fake_client = _FakeStructuredLlmClient(
        IntentResolution(resolved_question="q", retrieval_query="q")
    )
    resolver = IntentResolver(llm_client=fake_client)

    await resolver.resolve(question="What is type erasure?", memory_context=[])

    assert fake_client.received_output_model is IntentResolution
