from app import config
from app.providers.base import LLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.mock_provider import MockProvider


def get_provider(name: str | None = None) -> LLMProvider:
    name = (name or config.LLM_PROVIDER).lower()

    if name == "mock":
        return MockProvider()
    if name == "gemini":
        return GeminiProvider()
    if name in ("claude", "openai"):
        raise NotImplementedError(
            f"'{name}' provider is not implemented yet — 'mock' and 'gemini' are available so far. "
            "Set LLM_PROVIDER=mock or LLM_PROVIDER=gemini in .env."
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {name!r}")
