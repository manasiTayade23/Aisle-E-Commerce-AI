import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# LLM Provider constants (avoiding circular import)
LLM_PROVIDER_ANTHROPIC = "anthropic"
LLM_PROVIDER_GEMINI = "gemini"
LLM_PROVIDER_OPENAI = "openai"

# FakeStoreAPI Configuration
FAKE_STORE_BASE_URL = os.getenv("FAKE_STORE_BASE_URL", "https://fakestoreapi.com")
FAKE_STORE_TIMEOUT = float(os.getenv("FAKE_STORE_TIMEOUT", "15.0"))

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model names (provider-specific defaults)
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# LLM Generation Parameters
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shopping_assistant.db")

# Vector Database Configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")  # chroma or qdrant
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Conversation persistence (Redis per session; omit for in-memory)
REDIS_URL = os.getenv("REDIS_URL", "")  # e.g. redis://localhost:6379/0
CONVERSATION_TTL_SECONDS = int(os.getenv("CONVERSATION_TTL_SECONDS", "86400"))  # 24h

# Authentication
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET", "")
NEXTAUTH_URL = os.getenv("NEXTAUTH_URL", "http://localhost:3000")
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("NEXTAUTH_SECRET", "change-me-in-production"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7  # 7 days


def get_llm_config(provider: str = None) -> dict:
    """Get LLM configuration for a specific provider."""
    provider = (provider or LLM_PROVIDER).lower()
    
    if provider == LLM_PROVIDER_ANTHROPIC:
        return {
            "provider": LLM_PROVIDER_ANTHROPIC,
            "api_key": ANTHROPIC_API_KEY,
            "model": ANTHROPIC_MODEL,
        }
    elif provider == LLM_PROVIDER_GEMINI:
        return {
            "provider": LLM_PROVIDER_GEMINI,
            "api_key": GEMINI_API_KEY,
            "model": GEMINI_MODEL,
        }
    elif provider == LLM_PROVIDER_OPENAI:
        return {
            "provider": LLM_PROVIDER_OPENAI,
            "api_key": OPENAI_API_KEY,
            "model": OPENAI_MODEL,
        }
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_default_llm_config() -> dict:
    """Get default LLM configuration."""
    return get_llm_config(LLM_PROVIDER)
