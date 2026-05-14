from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from conan.llm import query_structured


class _TestModel(BaseModel):
    value: str


def test_query_structured_uses_ollama_by_default(monkeypatch):
    monkeypatch.delenv("CONAN_LLM_PROVIDER", raising=False)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _TestModel(value="ok")

    with patch("conan.llm._get_ollama_client", return_value=mock_client):
        result = query_structured("sys", "usr", _TestModel)

    mock_client.chat.completions.create.assert_called_once()
    assert result.value == "ok"


def test_query_structured_uses_default_model(monkeypatch):
    monkeypatch.delenv("CONAN_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("CONAN_SKILL_MODEL", raising=False)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _TestModel(value="ok")

    with patch("conan.llm._get_ollama_client", return_value=mock_client):
        query_structured("sys", "usr", _TestModel)

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gemma4:e4b"


def test_query_structured_respects_model_override(monkeypatch):
    monkeypatch.delenv("CONAN_LLM_PROVIDER", raising=False)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _TestModel(value="ok")

    with patch("conan.llm._get_ollama_client", return_value=mock_client):
        query_structured("sys", "usr", _TestModel, model="gemma4:26b")

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gemma4:26b"
