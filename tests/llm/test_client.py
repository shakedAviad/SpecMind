from typing import Any

import pytest
from pydantic import SecretStr

from app.config.settings import Settings
from app.llm.client import LlmStructuredOutputError, OpenAiLlmClient, create_chat_model
from app.models.outputs import ReasoningResult


class _FakeStructuredRunnable:
    def __init__(self, result: Any) -> None:
        self._result = result
        self.received_input: Any = None

    async def ainvoke(self, input: Any) -> Any:
        self.received_input = input
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class _FakeChatModel:
    def __init__(self, result: Any) -> None:
        self._runnable = _FakeStructuredRunnable(result)
        self.requested_schema: type | None = None

    def with_structured_output(self, schema: type) -> _FakeStructuredRunnable:
        self.requested_schema = schema
        return self._runnable


async def test_generate_structured_returns_validated_model() -> None:
    expected = ReasoningResult(
        relevant_points=["point one"],
        conclusion="conclusion text",
        source_chunk_indexes=[0, 1],
    )
    fake_model = _FakeChatModel(expected)
    llm_client = OpenAiLlmClient(model=fake_model)

    result = await llm_client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        output_model=ReasoningResult,
    )

    assert result == expected


async def test_generate_structured_binds_the_requested_output_model_as_schema() -> None:
    expected = ReasoningResult(
        relevant_points=[], conclusion="conclusion text", source_chunk_indexes=[]
    )
    fake_model = _FakeChatModel(expected)
    llm_client = OpenAiLlmClient(model=fake_model)

    await llm_client.generate_structured(
        system_prompt="system-prompt",
        user_prompt="user-prompt",
        output_model=ReasoningResult,
    )

    assert fake_model.requested_schema is ReasoningResult
    assert fake_model._runnable.received_input == [
        ("system", "system-prompt"),
        ("human", "user-prompt"),
    ]


async def test_generate_structured_raises_when_result_is_not_the_output_model() -> None:
    fake_model = _FakeChatModel({"not": "a reasoning result"})
    llm_client = OpenAiLlmClient(model=fake_model)

    with pytest.raises(LlmStructuredOutputError):
        await llm_client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            output_model=ReasoningResult,
        )


async def test_generate_structured_raises_when_the_underlying_call_fails() -> None:
    fake_model = _FakeChatModel(RuntimeError("provider unavailable"))
    llm_client = OpenAiLlmClient(model=fake_model)

    with pytest.raises(LlmStructuredOutputError):
        await llm_client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            output_model=ReasoningResult,
        )


def test_create_chat_model_uses_model_and_api_key_from_settings() -> None:
    settings = Settings(openai_api_key="sk-test", openai_model="gpt-4.1")

    chat_model = create_chat_model(settings)

    assert chat_model.model_name == "gpt-4.1"
    assert isinstance(chat_model.openai_api_key, SecretStr)
    assert chat_model.openai_api_key.get_secret_value() == "sk-test"
