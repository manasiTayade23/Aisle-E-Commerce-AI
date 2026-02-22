"""LLM factory for creating LLM instances."""

from app.llm.base import BaseLLM, LLMProvider
from app.llm.anthropic_llm import AnthropicLLM
from app.llm.gemini_llm import GeminiLLM
from app.llm.openai_llm import OpenAILLM
from app.config import (
    get_llm_config,
    ANTHROPIC_MODEL,
    GEMINI_MODEL,
    OPENAI_MODEL,
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_GEMINI,
    LLM_PROVIDER_OPENAI,
)


def create_llm(provider: str = None, api_key: str = None, model: str = None) -> BaseLLM:
    """
    Create an LLM instance based on provider.
    
    Args:
        provider: LLM provider name (anthropic, gemini, openai)
        api_key: API key for the provider (uses env if not provided)
        model: Model name (uses env default if not provided)
    
    Returns:
        BaseLLM instance
    """
    config = get_llm_config(provider)
    
    provider_name = provider or config["provider"]
    api_key = api_key or config["api_key"]
    # Use model from parameter, then config, then env defaults
    if not model:
        model = config.get("model")
        if not model:
            # Fallback to env defaults
            if provider_name == LLM_PROVIDER_ANTHROPIC or provider_name == LLMProvider.ANTHROPIC:
                model = ANTHROPIC_MODEL
            elif provider_name == LLM_PROVIDER_GEMINI or provider_name == LLMProvider.GEMINI:
                model = GEMINI_MODEL
            elif provider_name == LLM_PROVIDER_OPENAI or provider_name == LLMProvider.OPENAI:
                model = OPENAI_MODEL
    
    if provider_name == LLM_PROVIDER_ANTHROPIC or provider_name == LLMProvider.ANTHROPIC:
        return AnthropicLLM(api_key=api_key, model=model)
    elif provider_name == LLM_PROVIDER_GEMINI or provider_name == LLMProvider.GEMINI:
        return GeminiLLM(api_key=api_key, model=model)
    elif provider_name == LLM_PROVIDER_OPENAI or provider_name == LLMProvider.OPENAI:
        return OpenAILLM(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
