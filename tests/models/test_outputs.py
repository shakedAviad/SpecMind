import pytest
from pydantic import ValidationError

from app.models.outputs import ReasoningResult


def test_reasoning_result_accepts_valid_fields() -> None:
    reasoning = ReasoningResult(
        relevant_points=["A variable of primitive type holds a value of that type."],
        conclusion="Primitive types are not object references.",
        source_chunk_indexes=[0, 2],
    )

    assert reasoning.relevant_points == ["A variable of primitive type holds a value of that type."]
    assert reasoning.conclusion == "Primitive types are not object references."
    assert reasoning.source_chunk_indexes == [0, 2]


def test_reasoning_result_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        ReasoningResult(relevant_points=[], source_chunk_indexes=[])


def test_reasoning_result_rejects_wrong_type_for_source_chunk_indexes() -> None:
    with pytest.raises(ValidationError):
        ReasoningResult(
            relevant_points=[],
            conclusion="conclusion",
            source_chunk_indexes=["not-an-int"],
        )
