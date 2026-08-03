import uuid

from qdrant_client import AsyncQdrantClient, models

from app.config.settings import Settings
from app.llm.embeddings import EmbeddingClient
from app.models.retrieval import RetrievedChunk

_INGEST_BATCH_SIZE = 100


def create_qdrant_client(settings: Settings) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=settings.qdrant_url)


class VectorSearch:
    def __init__(
        self,
        client: AsyncQdrantClient,
        embedding_client: EmbeddingClient,
        collection_name: str,
        vector_size: int,
    ) -> None:
        self._client = client
        self._embedding_client = embedding_client
        self._collection_name = collection_name
        self._vector_size = vector_size

    async def ensure_collection(self) -> None:
        if await self._client.collection_exists(self._collection_name):
            return

        await self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=models.VectorParams(
                size=self._vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    async def ingest(self, chunks: list[RetrievedChunk]) -> None:
        if not chunks:
            return

        for start in range(0, len(chunks), _INGEST_BATCH_SIZE):
            batch = chunks[start : start + _INGEST_BATCH_SIZE]
            vectors = await self._embedding_client.embed([chunk.text for chunk in batch])

            points = [
                models.PointStruct(
                    id=_point_id(chunk.chunk_id),
                    vector=vector,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "document": chunk.document,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                    },
                )
                for chunk, vector in zip(batch, vectors, strict=True)
            ]

            await self._client.upsert(collection_name=self._collection_name, points=points)

    async def search(self, query: str, limit: int = 5) -> list[RetrievedChunk]:
        [query_vector] = await self._embedding_client.embed([query])

        result = await self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            limit=limit,
        )

        return [_to_chunk(point) for point in result.points]


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def _to_chunk(point: models.ScoredPoint) -> RetrievedChunk:
    payload = point.payload
    if payload is None:
        raise ValueError(f"Qdrant point {point.id} is missing its payload")

    return RetrievedChunk(
        chunk_id=payload["chunk_id"],
        document=payload["document"],
        chunk_index=payload["chunk_index"],
        text=payload["text"],
        score=point.score,
    )
