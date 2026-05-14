"""LLM client abstraction — Ollama (default) or Anthropic, via instructor."""
from __future__ import annotations
import os
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_RETRIES = 3

_ollama_client: object | None = None


def get_provider() -> str:
    return os.environ.get("CONAN_LLM_PROVIDER", "ollama").lower()


def _get_ollama_client() -> object:
    global _ollama_client
    if _ollama_client is None:
        from openai import OpenAI
        import instructor
        _ollama_client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama", timeout=600),
            mode=instructor.Mode.JSON,
        )
    return _ollama_client


def query_structured(
    system: str,
    user: str,
    response_model: Type[T],
    model: str | None = None,
    max_tokens: int = 2048,
) -> T:
    """Call the LLM and return a validated Pydantic response via instructor."""
    provider = get_provider()

    if model is None:
        if provider == "anthropic":
            model = ANTHROPIC_DEFAULT_MODEL
        else:
            model = os.environ.get("CONAN_SKILL_MODEL", "gemma4:e4b")

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    if provider == "anthropic":
        import anthropic
        import instructor
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required when CONAN_LLM_PROVIDER=anthropic")
        client = instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            response_model=response_model,
            max_retries=MAX_RETRIES,
        )

    client = _get_ollama_client()
    return client.chat.completions.create(
        model=model,
        messages=messages,
        response_model=response_model,
        max_retries=MAX_RETRIES,
        temperature=0,
        max_tokens=max_tokens,
        extra_body={"num_ctx": 16384, "num_predict": max_tokens},
    )
