from typing import Protocol

from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from app.config.settings import Settings


def create_embeddings_model(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
        api_key=SecretStr(settings.openai_api_key),
    )


class EmbeddingClient(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAiEmbeddingClient:
    def __init__(self, model: OpenAIEmbeddings) -> None:
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._model.aembed_documents(texts)
