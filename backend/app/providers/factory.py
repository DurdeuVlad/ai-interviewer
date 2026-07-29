from app import config
from app.providers.base import LLMProvider
from app.providers.mock_provider import MockProvider


def get_provider(name: str | None = None) -> LLMProvider:
    name = (name or config.LLM_PROVIDER).lower()

    if name == "mock":
        return MockProvider()
    if name in ("claude", "gemini", "openai"):
        raise NotImplementedError(
            f"'{name}' provider is not implemented yet — only 'mock' is available so far. "
            "Set LLM_PROVIDER=mock in .env."
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {name!r}")
