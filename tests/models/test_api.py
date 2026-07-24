import pytest
from pydantic import ValidationError

from app.models.api import AskRequest, AskResponse, HealthStatus


def test_ask_request_accepts_valid_fields() -> None:
    request = AskRequest(session_id="session-1", question="What is type erasure?")

    assert request.session_id == "session-1"
    assert request.question == "What is type erasure?"


def test_ask_request_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        AskRequest(session_id="session-1")


def test_ask_response_accepts_valid_fields() -> None:
    response = AskResponse(answer="Generic array creation is prohibited because ...")

    assert response.answer == "Generic array creation is prohibited because ..."


def test_ask_response_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        AskResponse()


def test_health_status_accepts_valid_fields() -> None:
    status = HealthStatus(status="ok")

    assert status.status == "ok"


def test_health_status_rejects_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        HealthStatus()
