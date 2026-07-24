from typing import Any

from app.conversation.understanding import ConversationUnderstanding
from app.models.outputs import ConversationUnderstandingResult


class _FakeStructuredLlmClient:
    def __init__(self, result: ConversationUnderstandingResult) -> None:
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


async def test_understand_returns_the_llm_result_for_a_follow_up() -> None:
    fake_client = _FakeStructuredLlmClient(
        ConversationUnderstandingResult(
            is_follow_up=True,
            missing_context="the earlier topic or rule to compare with arrays",
        )
    )
    understanding = ConversationUnderstanding(llm_client=fake_client)

    result = await understanding.understand("What about arrays?")

    assert result.is_follow_up is True
    assert result.standalone_question is None
    assert result.missing_context == "the earlier topic or rule to compare with arrays"


async def test_understand_returns_the_llm_result_for_a_standalone_question() -> None:
    fake_client = _FakeStructuredLlmClient(
        ConversationUnderstandingResult(
            is_follow_up=False,
            standalone_question="What is type erasure?",
        )
    )
    understanding = ConversationUnderstanding(llm_client=fake_client)

    result = await understanding.understand("What is type erasure?")

    assert result.is_follow_up is False
    assert result.standalone_question == "What is type erasure?"
    assert result.missing_context is None


async def test_understand_passes_the_question_in_the_user_prompt() -> None:
    fake_client = _FakeStructuredLlmClient(ConversationUnderstandingResult(is_follow_up=False))
    understanding = ConversationUnderstanding(llm_client=fake_client)

    await understanding.understand("What is type erasure?")

    assert fake_client.received_user_prompt == "Classify this question:\n\nWhat is type erasure?"
    assert fake_client.received_output_model is ConversationUnderstandingResult
