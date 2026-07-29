from app import config
from app.providers.base import LLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAIProvider


def get_provider(name: str | None = None) -> LLMProvider:
    name = (name or config.LLM_PROVIDER).lower()

    if name == "mock":
        return MockProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "openai":
        return OpenAIProvider()
    if name == "claude":
        raise NotImplementedError(
            "'claude' provider is not implemented yet — 'mock', 'gemini', and 'openai' are "
            "available so far. Set LLM_PROVIDER accordingly in .env."
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {name!r}")
