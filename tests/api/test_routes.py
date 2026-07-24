from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.container import AppContainer
from app.graph.state import GraphState
from app.memory.store import MemoryStore


class _FakeGraph:
    def __init__(self, result: dict[str, Any]) -> None:
        self._result = result
        self.received_state: GraphState | None = None

    async def ainvoke(self, state: GraphState) -> dict[str, Any]:
        self.received_state = state
        return self._result


def _build_test_app(graph: _FakeGraph) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.state.container = AppContainer(
        graph=graph,
        memory_store=MemoryStore(),
        hybrid_search=None,
    )
    return app


def test_ask_returns_the_graph_answer_and_echoes_the_provided_session_id() -> None:
    fake_graph = _FakeGraph({"answer": "Generic array creation is prohibited because ..."})
    client = TestClient(_build_test_app(fake_graph))

    response = client.post(
        "/ask",
        json={
            "session_id": "session-1",
            "question": "Why is generic array creation prohibited?",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-1",
        "answer": "Generic array creation is prohibited because ...",
    }


def test_ask_generates_a_session_id_when_none_is_provided() -> None:
    fake_graph = _FakeGraph({"answer": "an answer"})
    client = TestClient(_build_test_app(fake_graph))

    response = client.post("/ask", json={"question": "What is type erasure?"})

    assert response.status_code == 200
    generated_session_id = response.json()["session_id"]
    assert generated_session_id
    assert fake_graph.received_state is not None
    assert fake_graph.received_state["session_id"] == generated_session_id


def test_ask_invokes_the_graph_with_the_initial_state() -> None:
    fake_graph = _FakeGraph({"answer": "an answer"})
    client = TestClient(_build_test_app(fake_graph))

    client.post("/ask", json={"session_id": "session-1", "question": "What is type erasure?"})

    assert fake_graph.received_state is not None
    assert fake_graph.received_state["session_id"] == "session-1"
    assert fake_graph.received_state["original_question"] == "What is type erasure?"
    assert fake_graph.received_state["retry_count"] == 0


def test_ask_returns_500_when_the_graph_produces_no_answer() -> None:
    fake_graph = _FakeGraph({})
    client = TestClient(_build_test_app(fake_graph))

    response = client.post("/ask", json={"session_id": "session-1", "question": "a question"})

    assert response.status_code == 500


def test_ask_rejects_a_request_missing_the_question_field() -> None:
    fake_graph = _FakeGraph({"answer": "unused"})
    client = TestClient(_build_test_app(fake_graph))

    response = client.post("/ask", json={"session_id": "session-1"})

    assert response.status_code == 422
