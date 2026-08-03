from langgraph.graph.state import CompiledStateGraph

from app.graph.builder import _route_after_context_evaluation, build_graph
from app.graph.state import GraphState, create_initial_state
from app.models.outputs import (
    ContextEvaluationResult,
    ConversationUnderstandingResult,
    IntentResolution,
    QueryRewriteResult,
    ReasoningResult,
)
from app.models.retrieval import RetrievedChunk
from app.nodes.context_evaluation import ContextEvaluationNode
from app.nodes.conversation_understanding import ConversationUnderstandingNode
from app.nodes.generation import GenerationNode
from app.nodes.memory_retrieval import MemoryRetrievalNode
from app.nodes.persist_memory import PersistMemoryNode
from app.nodes.reasoning import ReasoningNode
from app.nodes.rerank import RerankNode
from app.nodes.resolve_intent import ResolveIntentNode
from app.nodes.retrieve import RetrieveNode
from app.nodes.rewrite_retrieval_query import RewriteRetrievalQueryNode

_CHUNKS = [
    RetrievedChunk(chunk_id="jls25-0", document="jls25", chunk_index=0, text="chunk zero text"),
]


class _FakeConversationUnderstanding:
    async def understand(self, question: str) -> ConversationUnderstandingResult:
        return ConversationUnderstandingResult(is_follow_up=False, standalone_question=question)


class _FakeMemoryStore:
    def __init__(self) -> None:
        self.added_facts: list[tuple[str, list[str]]] = []

    async def get_context(self, session_id: str) -> list[str]:
        return []

    async def add_facts(self, session_id: str, facts: list[str]) -> None:
        self.added_facts.append((session_id, facts))


class _FakeIntentResolver:
    async def resolve(self, question: str, memory_context: list[str]) -> IntentResolution:
        return IntentResolution(resolved_question=question, retrieval_query=question)


class _FakeHybridSearch:
    def __init__(self) -> None:
        self.call_count = 0

    async def search(self, query: str) -> list[RetrievedChunk]:
        self.call_count += 1
        return _CHUNKS


class _FakeLlmReranker:
    def __init__(self) -> None:
        self.call_count = 0

    async def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        self.call_count += 1
        return chunks


class _FakeContextEvaluator:
    def __init__(self, results: list[ContextEvaluationResult]) -> None:
        self._results = list(results)
        self.call_count = 0

    async def evaluate(
        self, question: str, chunks: list[RetrievedChunk]
    ) -> ContextEvaluationResult:
        self.call_count += 1
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


class _FakeRetrievalQueryRewriter:
    def __init__(self) -> None:
        self.call_count = 0

    async def rewrite(
        self,
        question: str,
        previous_query: str,
        missing_information: str | None,
    ) -> QueryRewriteResult:
        self.call_count += 1
        return QueryRewriteResult(retrieval_query=f"rewritten query {self.call_count}")


class _FakeReasoningService:
    def __init__(self) -> None:
        self.call_count = 0

    async def reason(self, question: str, chunks: list[RetrievedChunk]) -> ReasoningResult:
        self.call_count += 1
        return ReasoningResult(
            relevant_points=["a point"], conclusion="a conclusion", source_chunk_indexes=[0]
        )


class _FakeAnswerGenerator:
    def __init__(self) -> None:
        self.call_count = 0

    async def generate(
        self,
        question: str,
        reasoning: ReasoningResult,
        chunks: list[RetrievedChunk],
    ) -> str:
        self.call_count += 1
        return "the final answer"


def _build_graph_with_fakes(
    context_evaluation_results: list[ContextEvaluationResult],
) -> tuple[
    CompiledStateGraph[GraphState, None, GraphState, GraphState],
    _FakeHybridSearch,
    _FakeLlmReranker,
    _FakeContextEvaluator,
    _FakeRetrievalQueryRewriter,
    _FakeReasoningService,
    _FakeAnswerGenerator,
    _FakeMemoryStore,
]:
    hybrid_search = _FakeHybridSearch()
    reranker = _FakeLlmReranker()
    context_evaluator = _FakeContextEvaluator(context_evaluation_results)
    query_rewriter = _FakeRetrievalQueryRewriter()
    reasoning_service = _FakeReasoningService()
    answer_generator = _FakeAnswerGenerator()
    memory_store = _FakeMemoryStore()

    graph = build_graph(
        conversation_understanding_node=ConversationUnderstandingNode(
            understanding=_FakeConversationUnderstanding()
        ),
        memory_retrieval_node=MemoryRetrievalNode(memory_store=memory_store),
        resolve_intent_node=ResolveIntentNode(resolver=_FakeIntentResolver()),
        retrieve_node=RetrieveNode(hybrid_search=hybrid_search),
        rerank_node=RerankNode(reranker=reranker),
        context_evaluation_node=ContextEvaluationNode(context_evaluator=context_evaluator),
        rewrite_retrieval_query_node=RewriteRetrievalQueryNode(query_rewriter=query_rewriter),
        reasoning_node=ReasoningNode(reasoning_service=reasoning_service),
        generation_node=GenerationNode(answer_generator=answer_generator),
        persist_memory_node=PersistMemoryNode(memory_store=memory_store),
    )

    return (
        graph,
        hybrid_search,
        reranker,
        context_evaluator,
        query_rewriter,
        reasoning_service,
        answer_generator,
        memory_store,
    )


async def test_graph_answers_directly_when_context_is_sufficient_on_the_first_try() -> None:
    (
        graph,
        hybrid_search,
        reranker,
        context_evaluator,
        query_rewriter,
        reasoning_service,
        answer_generator,
        memory_store,
    ) = _build_graph_with_fakes([ContextEvaluationResult(is_sufficient=True)])

    initial_state = create_initial_state(session_id="session-1", question="What is type erasure?")
    final_state = await graph.ainvoke(initial_state)

    assert final_state["answer"] == "the final answer"
    assert final_state["retry_count"] == 0
    assert hybrid_search.call_count == 1
    assert reranker.call_count == 1
    assert context_evaluator.call_count == 1
    assert query_rewriter.call_count == 0
    assert reasoning_service.call_count == 1
    assert answer_generator.call_count == 1
    assert memory_store.added_facts == [
        ("session-1", ["The user asked: What is type erasure? Conclusion: a conclusion"])
    ]


async def test_graph_retries_once_when_context_is_insufficient_then_succeeds() -> None:
    (
        graph,
        hybrid_search,
        reranker,
        context_evaluator,
        query_rewriter,
        reasoning_service,
        answer_generator,
        memory_store,
    ) = _build_graph_with_fakes(
        [
            ContextEvaluationResult(is_sufficient=False, missing_information="a gap"),
            ContextEvaluationResult(is_sufficient=True),
        ]
    )

    initial_state = create_initial_state(session_id="session-1", question="What about arrays?")
    final_state = await graph.ainvoke(initial_state)

    assert final_state["answer"] == "the final answer"
    assert final_state["retry_count"] == 1
    assert final_state["retrieval_query"] == "rewritten query 1"
    assert hybrid_search.call_count == 2
    assert reranker.call_count == 2
    assert context_evaluator.call_count == 2
    assert query_rewriter.call_count == 1
    assert reasoning_service.call_count == 1
    assert answer_generator.call_count == 1
    assert memory_store.added_facts == [
        ("session-1", ["The user asked: What about arrays? Conclusion: a conclusion"])
    ]


async def test_graph_does_not_retry_a_second_time_when_still_insufficient() -> None:
    (
        graph,
        hybrid_search,
        reranker,
        context_evaluator,
        query_rewriter,
        reasoning_service,
        answer_generator,
        memory_store,
    ) = _build_graph_with_fakes(
        [ContextEvaluationResult(is_sufficient=False, missing_information="still missing")]
    )

    initial_state = create_initial_state(session_id="session-1", question="What about arrays?")
    final_state = await graph.ainvoke(initial_state)

    assert final_state["answer"] == "the final answer"
    assert final_state["retry_count"] == 1
    assert hybrid_search.call_count == 2
    assert reranker.call_count == 2
    assert context_evaluator.call_count == 2
    assert query_rewriter.call_count == 1
    assert reasoning_service.call_count == 1
    assert answer_generator.call_count == 1
    assert memory_store.added_facts == [
        ("session-1", ["The user asked: What about arrays? Conclusion: a conclusion"])
    ]


def test_route_reasons_when_context_is_sufficient() -> None:
    route = _route_after_context_evaluation({"context_is_sufficient": True, "retry_count": 0})

    assert route == "reason"


def test_route_retries_when_insufficient_and_no_retry_used_yet() -> None:
    route = _route_after_context_evaluation({"context_is_sufficient": False, "retry_count": 0})

    assert route == "retry"


def test_route_reasons_when_insufficient_but_already_retried_once() -> None:
    route = _route_after_context_evaluation({"context_is_sufficient": False, "retry_count": 1})

    assert route == "reason"


def test_route_retries_when_sufficiency_is_missing_and_no_retry_used_yet() -> None:
    route = _route_after_context_evaluation({})

    assert route == "retry"


def test_route_reasons_when_sufficiency_is_missing_but_already_retried_once() -> None:
    route = _route_after_context_evaluation({"retry_count": 1})

    assert route == "reason"
