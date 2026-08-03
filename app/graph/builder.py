from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.state import GraphState
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


def build_graph(
    conversation_understanding_node: ConversationUnderstandingNode,
    memory_retrieval_node: MemoryRetrievalNode,
    resolve_intent_node: ResolveIntentNode,
    retrieve_node: RetrieveNode,
    rerank_node: RerankNode,
    context_evaluation_node: ContextEvaluationNode,
    rewrite_retrieval_query_node: RewriteRetrievalQueryNode,
    reasoning_node: ReasoningNode,
    generation_node: GenerationNode,
    persist_memory_node: PersistMemoryNode,
) -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:
    graph = StateGraph(GraphState)

    graph.add_node("conversation_understanding", conversation_understanding_node)
    graph.add_node("memory_retrieval", memory_retrieval_node)
    graph.add_node("resolve_intent", resolve_intent_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("context_evaluation", context_evaluation_node)
    graph.add_node("rewrite_retrieval_query", rewrite_retrieval_query_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("generation", generation_node)
    graph.add_node("persist_memory", persist_memory_node)

    graph.set_entry_point("conversation_understanding")
    graph.add_edge("conversation_understanding", "memory_retrieval")
    graph.add_edge("memory_retrieval", "resolve_intent")
    graph.add_edge("resolve_intent", "retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "context_evaluation")

    graph.add_conditional_edges(
        "context_evaluation",
        _route_after_context_evaluation,
        {
            "retry": "rewrite_retrieval_query",
            "reason": "reasoning",
        },
    )

    graph.add_edge("rewrite_retrieval_query", "retrieve")
    graph.add_edge("reasoning", "generation")
    graph.add_edge("generation", "persist_memory")
    graph.add_edge("persist_memory", END)

    return graph.compile()


def _route_after_context_evaluation(state: GraphState) -> str:
    if state.get("context_is_sufficient") is True:
        return "reason"

    if state.get("retry_count", 0) == 0:
        return "retry"

    return "reason"
