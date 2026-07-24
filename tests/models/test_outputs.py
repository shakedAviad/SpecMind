import pytest
from pydantic import ValidationError

from app.models.outputs import (
    ContextEvaluationResult,
    ConversationUnderstandingResult,
    IntentResolution,
    ReasoningResult,
    RerankResult,
)


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


def test_intent_resolution_accepts_valid_fields() -> None:
    intent_resolution = IntentResolution(
        resolved_question="Does type erasure also apply to arrays?",
        retrieval_query="type erasure arrays",
    )

    assert intent_resolution.resolved_question == "Does type erasure also apply to arrays?"
    assert intent_resolution.retrieval_query == "type erasure arrays"


def test_intent_resolution_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        IntentResolution(resolved_question="What is type erasure?")


def test_context_evaluation_result_accepts_sufficient_context() -> None:
    result = ContextEvaluationResult(is_sufficient=True)

    assert result.is_sufficient is True
    assert result.missing_information is None


def test_context_evaluation_result_accepts_insufficient_context() -> None:
    result = ContextEvaluationResult(
        is_sufficient=False,
        missing_information="the rule the question asks about",
    )

    assert result.is_sufficient is False
    assert result.missing_information == "the rule the question asks about"


def test_context_evaluation_result_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        ContextEvaluationResult()
