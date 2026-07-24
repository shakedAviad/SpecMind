from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.health import router


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_liveness_returns_ok_without_a_container() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_ok_when_the_container_is_set() -> None:
    app = _build_test_app()
    app.state.container = object()
    client = TestClient(app)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_503_when_the_container_is_not_set() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/health/ready")

    assert response.status_code == 503
