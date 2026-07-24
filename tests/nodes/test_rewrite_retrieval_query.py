from app.graph.state import GraphState
from app.models.outputs import QueryRewriteResult
from app.nodes.rewrite_retrieval_query import RewriteRetrievalQueryNode


class _FakeRetrievalQueryRewriter:
    def __init__(self, result: QueryRewriteResult) -> None:
        self._result = result
        self.received_question: str | None = None
        self.received_previous_query: str | None = None
        self.received_missing_information: str | None = None

    async def rewrite(
        self,
        question: str,
        previous_query: str,
        missing_information: str | None,
    ) -> QueryRewriteResult:
        self.received_question = question
        self.received_previous_query = previous_query
        self.received_missing_information = missing_information
        return self._result


async def test_node_invokes_rewriter_with_question_previous_query_and_missing_information() -> None:
    fake = _FakeRetrievalQueryRewriter(QueryRewriteResult(retrieval_query="new query"))
    node = RewriteRetrievalQueryNode(query_rewriter=fake)
    state: GraphState = {
        "resolved_question": "Why is generic array creation prohibited?",
        "retrieval_query": "generic array creation prohibited",
        "missing_information": "the reason the rule exists",
        "retry_count": 0,
    }

    await node(state)

    assert fake.received_question == "Why is generic array creation prohibited?"
    assert fake.received_previous_query == "generic array creation prohibited"
    assert fake.received_missing_information == "the reason the rule exists"


async def test_node_returns_the_new_query_and_increments_retry_count() -> None:
    fake = _FakeRetrievalQueryRewriter(QueryRewriteResult(retrieval_query="new query"))
    node = RewriteRetrievalQueryNode(query_rewriter=fake)
    state: GraphState = {
        "resolved_question": "a question",
        "retrieval_query": "old query",
        "missing_information": None,
        "retry_count": 0,
    }

    update = await node(state)

    assert update == {"retrieval_query": "new query", "retry_count": 1}


async def test_node_defaults_retry_count_to_zero_when_absent() -> None:
    fake = _FakeRetrievalQueryRewriter(QueryRewriteResult(retrieval_query="new query"))
    node = RewriteRetrievalQueryNode(query_rewriter=fake)
    state: GraphState = {
        "resolved_question": "a question",
        "retrieval_query": "old query",
    }

    update = await node(state)

    assert update["retry_count"] == 1
