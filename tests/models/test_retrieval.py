import pytest
from pydantic import ValidationError

from app.models.retrieval import RetrievedChunk


def test_retrieved_chunk_accepts_valid_fields() -> None:
    chunk = RetrievedChunk(
        chunk_id="jls-4.2-0",
        document="jls25",
        chunk_index=0,
        text="Primitive types are predefined by the Java programming language.",
        score=0.87,
    )

    assert chunk.chunk_id == "jls-4.2-0"
    assert chunk.document == "jls25"
    assert chunk.chunk_index == 0
    assert chunk.score == 0.87


def test_retrieved_chunk_score_defaults_to_none() -> None:
    chunk = RetrievedChunk(
        chunk_id="jls-4.2-0",
        document="jls25",
        chunk_index=0,
        text="Primitive types are predefined by the Java programming language.",
    )

    assert chunk.score is None


def test_retrieved_chunk_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        RetrievedChunk(document="jls25", chunk_index=0, text="text")


def test_retrieved_chunk_rejects_wrong_type_for_chunk_index() -> None:
    with pytest.raises(ValidationError):
        RetrievedChunk(
            chunk_id="jls-4.2-0",
            document="jls25",
            chunk_index="not-an-int",
            text="text",
        )
