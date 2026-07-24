from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    chunk_id: str
    document: str
    chunk_index: int
    text: str
    score: float | None = None
