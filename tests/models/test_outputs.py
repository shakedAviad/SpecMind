import pytest
from pydantic import ValidationError

from app.models.outputs import ConversationUnderstandingResult, ReasoningResult, RerankResult


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


def test_rerank_result_accepts_valid_indexes() -> None:
    rerank_result = RerankResult(relevant_chunk_indexes=[2, 0, 1])

    assert rerank_result.relevant_chunk_indexes == [2, 0, 1]


def test_rerank_result_accepts_empty_indexes() -> None:
    rerank_result = RerankResult(relevant_chunk_indexes=[])

    assert rerank_result.relevant_chunk_indexes == []


def test_rerank_result_rejects_wrong_type_for_relevant_chunk_indexes() -> None:
    with pytest.raises(ValidationError):
        RerankResult(relevant_chunk_indexes=["not-an-int"])


def test_conversation_understanding_result_accepts_a_standalone_question() -> None:
    result = ConversationUnderstandingResult(
        is_follow_up=False,
        standalone_question="What is type erasure?",
    )

    assert result.is_follow_up is False
    assert result.standalone_question == "What is type erasure?"
    assert result.missing_context is None


def test_conversation_understanding_result_accepts_a_follow_up() -> None:
    result = ConversationUnderstandingResult(
        is_follow_up=True,
        missing_context="the earlier topic being compared",
    )

    assert result.is_follow_up is True
    assert result.standalone_question is None
    assert result.missing_context == "the earlier topic being compared"


def test_conversation_understanding_result_defaults_optional_fields_to_none() -> None:
    result = ConversationUnderstandingResult(is_follow_up=False)

    assert result.standalone_question is None
    assert result.missing_context is None


def test_conversation_understanding_result_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        ConversationUnderstandingResult()
