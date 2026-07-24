from typing import Any

from app.models.outputs import QueryRewriteResult
from app.retrieval.query_rewriter import RetrievalQueryRewriter


class _FakeStructuredLlmClient:
    def __init__(self, result: QueryRewriteResult) -> None:
        self._result = result
        self.received_system_prompt: str | None = None
        self.received_user_prompt: str | None = None
        self.received_output_model: type | None = None

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[Any],
    ) -> Any:
        self.received_system_prompt = system_prompt
        self.received_user_prompt = user_prompt
        self.received_output_model = output_model
        return self._result


async def test_rewrite_returns_the_llm_result() -> None:
    fake_client = _FakeStructuredLlmClient(
        QueryRewriteResult(retrieval_query="reifiable types generic array creation")
    )
    rewriter = RetrievalQueryRewriter(llm_client=fake_client)

    result = await rewriter.rewrite(
        question="Why is generic array creation prohibited?",
        previous_query="generic array creation prohibited",
        missing_information="the reason the rule exists",
    )

    assert result.retrieval_query == "reifiable types generic array creation"


async def test_rewrite_includes_question_previous_query_and_missing_information() -> None:
    fake_client = _FakeStructuredLlmClient(QueryRewriteResult(retrieval_query="q"))
    rewriter = RetrievalQueryRewriter(llm_client=fake_client)

    await rewriter.rewrite(
        question="Does type erasure also apply to arrays?",
        previous_query="type erasure arrays",
        missing_information="whether the rule covers array component types",
    )

    assert fake_client.received_user_prompt is not None
    assert "Does type erasure also apply to arrays?" in fake_client.received_user_prompt
    assert "type erasure arrays" in fake_client.received_user_prompt
    assert "whether the rule covers array component types" in fake_client.received_user_prompt


async def test_rewrite_marks_absent_missing_information_explicitly() -> None:
    fake_client = _FakeStructuredLlmClient(QueryRewriteResult(retrieval_query="q"))
    rewriter = RetrievalQueryRewriter(llm_client=fake_client)

    await rewriter.rewrite(
        question="What is type erasure?",
        previous_query="type erasure",
        missing_information=None,
    )

    assert fake_client.received_user_prompt is not None
    assert "(not specified)" in fake_client.received_user_prompt


async def test_rewrite_uses_the_query_rewrite_result_model_as_the_output_schema() -> None:
    fake_client = _FakeStructuredLlmClient(QueryRewriteResult(retrieval_query="q"))
    rewriter = RetrievalQueryRewriter(llm_client=fake_client)

    await rewriter.rewrite(
        question="What is type erasure?",
        previous_query="type erasure",
        missing_information=None,
    )

    assert fake_client.received_output_model is QueryRewriteResult
