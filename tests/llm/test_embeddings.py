from typing import Any

from pydantic import SecretStr

from app.config.settings import Settings
from app.llm.embeddings import OpenAiEmbeddingClient, create_embeddings_model


class _FakeEmbeddingsModel:
    def __init__(self, vectors: list[list[float]]) -> None:
        self._vectors = vectors
        self.received_texts: list[str] | None = None

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        self.received_texts = texts
        return self._vectors


async def test_embed_returns_vectors_from_the_underlying_model() -> None:
    fake_model = _FakeEmbeddingsModel([[0.1, 0.2], [0.3, 0.4]])
    embedding_client = OpenAiEmbeddingClient(model=fake_model)

    vectors = await embedding_client.embed(["first chunk", "second chunk"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert fake_model.received_texts == ["first chunk", "second chunk"]


def test_create_embeddings_model_uses_model_and_dimensions_from_settings() -> None:
    settings = Settings(
        openai_api_key="sk-test",
        openai_embedding_model="text-embedding-3-large",
        openai_embedding_dimensions=256,
    )

    embeddings_model = create_embeddings_model(settings)

    assert embeddings_model.model == "text-embedding-3-large"
    assert embeddings_model.dimensions == 256
    api_key: Any = embeddings_model.openai_api_key
    assert isinstance(api_key, SecretStr)
    assert api_key.get_secret_value() == "sk-test"
