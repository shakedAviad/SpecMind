from app.graph.state import create_initial_state


def test_create_initial_state_sets_required_fields() -> None:
    state = create_initial_state(session_id="session-1", question="What is a primitive type?")

    assert state["session_id"] == "session-1"
    assert state["original_question"] == "What is a primitive type?"
    assert state["retry_count"] == 0


def test_create_initial_state_does_not_set_downstream_fields() -> None:
    state = create_initial_state(session_id="session-1", question="What is a primitive type?")

    assert "resolved_question" not in state
    assert "retrieval_query" not in state
    assert "retrieved_chunks" not in state
    assert "reranked_chunks" not in state
    assert "reasoning" not in state
    assert "answer" not in state


def test_create_initial_state_is_independent_between_calls() -> None:
    first = create_initial_state(session_id="session-1", question="Q1")
    second = create_initial_state(session_id="session-2", question="Q2")

    first["answer"] = "mutated"

    assert "answer" not in second
