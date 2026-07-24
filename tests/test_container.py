from pathlib import Path

from qdrant_client import AsyncQdrantClient

from app.config.settings import Settings
from app.container import create_app_container
from app.memory.store import MemoryStore
from app.retrieval.hybrid_search import HybridSearch

_JLS_PDF_PATH = Path(__file__).resolve().parents[1] / "data" / "jls25.pdf"


async def test_create_app_container_wires_a_usable_container() -> None:
    settings = Settings(
        openai_api_key="sk-test",
        jls_pdf_path=str(_JLS_PDF_PATH),
        qdrant_collection_name="container_test_collection",
    )
    qdrant_client = AsyncQdrantClient(location=":memory:")

    container = await create_app_container(settings, qdrant_client=qdrant_client)

    assert container.graph is not None
    assert isinstance(container.memory_store, MemoryStore)
    assert isinstance(container.hybrid_search, HybridSearch)
    assert await qdrant_client.collection_exists("container_test_collection")

    await container.memory_store.add_facts("session-1", ["a remembered fact"])
    assert await container.memory_store.get_context("session-1") == ["a remembered fact"]

    await qdrant_client.close()
