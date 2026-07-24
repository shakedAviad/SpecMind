import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_settings_uses_default_model_when_env_var_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    settings = Settings()

    assert settings.openai_api_key == "sk-test"
    assert settings.openai_model == "gpt-4.1-mini"


def test_settings_reads_model_override_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1")

    settings = Settings()

    assert settings.openai_model == "gpt-4.1"


def test_settings_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(ValidationError):
        Settings()
