from pydantic import BaseModel


class ReasoningResult(BaseModel):
    relevant_points: list[str]
    conclusion: str
    source_chunk_indexes: list[int]
