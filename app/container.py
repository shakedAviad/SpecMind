from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from qdrant_client import AsyncQdrantClient

from app.chunking.chunker import chunk_pages
from app.chunking.pdf_loader import load_pdf_pages
from app.config.settings import Settings
from app.conversation.understanding import ConversationUnderstanding
from app.evaluation.context_evaluator import ContextEvaluator
from app.generation.answer_generator import AnswerGenerator
from app.graph.builder import build_graph
from app.graph.state import GraphState
from app.intent.resolver import IntentResolver
from app.llm.client import OpenAiLlmClient, create_chat_model
from app.llm.embeddings import OpenAiEmbeddingClient, create_embeddings_model
from app.memory.store import MemoryStore
from app.nodes.context_evaluation import ContextEvaluationNode
from app.nodes.conversation_understanding import ConversationUnderstandingNode
from app.nodes.generation import GenerationNode
from app.nodes.memory_retrieval import MemoryRetrievalNode
from app.nodes.reasoning import ReasoningNode
from app.nodes.rerank import RerankNode
from app.nodes.resolve_intent import ResolveIntentNode
from app.nodes.retrieve import RetrieveNode
from app.nodes.rewrite_retrieval_query import RewriteRetrievalQueryNode
from app.reasoning.service import ReasoningService
from app.reranking.llm_reranker import LlmReranker
from app.retrieval.bm25_search import Bm25Search
from app.retrieval.hybrid_search import HybridSearch
from app.retrieval.query_rewriter import RetrievalQueryRewriter
from app.retrieval.vector_search import VectorSearch, create_qdrant_client


@dataclass
class AppContainer:
    graph: CompiledStateGraph[GraphState, None, GraphState, GraphState]
    memory_store: MemoryStore
    hybrid_search: HybridSearch


async def create_app_container(
    settings: Settings,
    qdrant_client: AsyncQdrantClient | None = None,
) -> AppContainer:
    chat_model = create_chat_model(settings)
    llm_client = OpenAiLlmClient(model=chat_model)

    embeddings_model = create_embeddings_model(settings)
    embedding_client = OpenAiEmbeddingClient(model=embeddings_model)

    vector_search = VectorSearch(
        client=qdrant_client or create_qdrant_client(settings),
        embedding_client=embedding_client,
        collection_name=settings.qdrant_collection_name,
        vector_size=settings.openai_embedding_dimensions,
    )
    await vector_search.ensure_collection()

    pages = load_pdf_pages(settings.jls_pdf_path)
    chunks = chunk_pages(pages, document="jls25")
    bm25_search = Bm25Search()
    bm25_search.index(chunks)

    memory_store = MemoryStore()
    hybrid_search = HybridSearch(vector_search=vector_search, bm25_search=bm25_search)

    reranker = LlmReranker(llm_client=llm_client)
    understanding = ConversationUnderstanding(llm_client=llm_client)
    resolver = IntentResolver(llm_client=llm_client)
    context_evaluator = ContextEvaluator(llm_client=llm_client)
    query_rewriter = RetrievalQueryRewriter(llm_client=llm_client)
    reasoning_service = ReasoningService(llm_client=llm_client)
    answer_generator = AnswerGenerator(llm_client=llm_client)

    graph = build_graph(
        conversation_understanding_node=ConversationUnderstandingNode(understanding=understanding),
        memory_retrieval_node=MemoryRetrievalNode(memory_store=memory_store),
        resolve_intent_node=ResolveIntentNode(resolver=resolver),
        retrieve_node=RetrieveNode(hybrid_search=hybrid_search),
        rerank_node=RerankNode(reranker=reranker),
        context_evaluation_node=ContextEvaluationNode(context_evaluator=context_evaluator),
        rewrite_retrieval_query_node=RewriteRetrievalQueryNode(query_rewriter=query_rewriter),
        reasoning_node=ReasoningNode(reasoning_service=reasoning_service),
        generation_node=GenerationNode(answer_generator=answer_generator),
    )

    return AppContainer(graph=graph, memory_store=memory_store, hybrid_search=hybrid_search)
