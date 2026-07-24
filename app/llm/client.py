from typing import Protocol, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LlmStructuredOutputError(Exception):
    """Raised when the LLM does not return valid structured output."""


class StructuredLlmClient(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T: ...


class OpenAiLlmClient:
    def __init__(self, model: ChatOpenAI) -> None:
        self._model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        structured_model = self._model.with_structured_output(output_model)

        try:
            result = await structured_model.ainvoke(
                [
                    ("system", system_prompt),
                    ("human", user_prompt),
                ]
            )
        except Exception as error:
            raise LlmStructuredOutputError(
                f"LLM call failed while generating {output_model.__name__}"
            ) from error

        if not isinstance(result, output_model):
            raise LlmStructuredOutputError(
                f"LLM returned invalid structured output for {output_model.__name__}"
            )

        return result
