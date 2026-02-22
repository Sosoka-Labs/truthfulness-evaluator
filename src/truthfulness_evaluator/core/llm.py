"""Centralized LLM provider factory."""

from langchain_core.language_models import BaseChatModel

from .logging_config import get_logger

logger = get_logger()

# TODO: Extend with Bedrock, Ollama, etc.

_ANTHROPIC_HINTS = ("claude", "anthropic")
_OPENAI_HINTS = ("gpt", "o1", "o3", "o4", "openai")


def _detect_provider(model_name: str, **kwargs: object) -> str:
    """Detect LLM provider from model name.

    Returns:
        Provider key: "anthropic", "openai", or "openai-compatible".

    Raises:
        ValueError: If provider cannot be determined.
    """
    model_lower = model_name.lower()

    if any(hint in model_lower for hint in _ANTHROPIC_HINTS):
        return "anthropic"

    if any(hint in model_lower for hint in _OPENAI_HINTS):
        return "openai"

    if "base_url" in kwargs:
        return "openai-compatible"

    raise ValueError(
        f"Cannot determine provider for model '{model_name}'. "
        f"Expected model name containing one of {_ANTHROPIC_HINTS + _OPENAI_HINTS}, "
        f"or pass 'base_url' for OpenAI-compatible APIs."
    )


def create_chat_model(
    model_name: str,
    temperature: float = 0,
    **kwargs,
) -> BaseChatModel:
    """Create a chat model instance from a model name string.

    Centralizes the OpenAI vs. Anthropic routing logic that was
    previously scattered across 5+ files.

    Args:
        model_name: Model identifier (e.g., "gpt-4o", "claude-sonnet-4-5").
        temperature: Sampling temperature.
        **kwargs: Additional model-specific parameters. Pass ``base_url``
            for OpenAI-compatible providers (Ollama, vLLM, etc.).

    Returns:
        Configured BaseChatModel instance.

    Raises:
        ValueError: If provider cannot be determined from model name.
    """
    provider = _detect_provider(model_name, **kwargs)
    logger.debug("Creating %s model: %s", provider, model_name)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, temperature=temperature, **kwargs)

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model_name, temperature=temperature, **kwargs)
