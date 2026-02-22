# Environment Variables Reference

All configuration values are now loaded from environment variables. This document lists all available environment variables and their purposes.

## LLM Configuration

### Provider Selection
- `LLM_PROVIDER` - LLM provider to use (default: `anthropic`)
  - Options: `anthropic`, `gemini`, `openai`

### Anthropic Claude
- `ANTHROPIC_API_KEY` - Your Anthropic API key (required if using Anthropic)
- `ANTHROPIC_MODEL` - Claude model name (default: `claude-sonnet-4-20250514`)

### Google Gemini
- `GEMINI_API_KEY` - Your Google Gemini API key (required if using Gemini)
- `GEMINI_MODEL` - Gemini model name (default: `gemini-2.0-flash-exp`)

### OpenAI
- `OPENAI_API_KEY` - Your OpenAI API key (required if using OpenAI)
- `OPENAI_MODEL` - OpenAI model name (default: `gpt-4o`)

### LLM Generation Parameters
- `LLM_MAX_TOKENS` - Maximum tokens for LLM responses (default: `4096`)

## FakeStoreAPI Configuration

- `FAKE_STORE_BASE_URL` - Base URL for FakeStoreAPI (default: `https://fakestoreapi.com`)
- `FAKE_STORE_TIMEOUT` - Request timeout in seconds (default: `15.0`)

## Database Configuration

- `DATABASE_URL` - Database connection string (default: `sqlite:///./shopping_assistant.db`)
  - SQLite example: `sqlite:///./shopping_assistant.db`
  - PostgreSQL example: `postgresql://user:password@localhost/shopping_assistant`

## Vector Database Configuration

- `VECTOR_DB_TYPE` - Vector database type (default: `chroma`)
  - Options: `chroma`, `qdrant` (qdrant support coming soon)
- `CHROMA_PERSIST_DIR` - ChromaDB persistence directory (default: `./chroma_db`)
- `QDRANT_URL` - Qdrant server URL (default: `http://localhost:6333`)

## Embedding Configuration

- `EMBEDDING_MODEL` - Sentence transformer model for embeddings (default: `sentence-transformers/all-MiniLM-L6-v2`)
  - Other options: `sentence-transformers/all-mpnet-base-v2`, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## Backend Configuration

- `BACKEND_HOST` - Backend host address (default: `0.0.0.0`)
- `BACKEND_PORT` - Backend port (default: `8000`)

## Frontend Configuration

- `NEXT_PUBLIC_API_URL` - Backend API URL for frontend (default: `http://localhost:8000`)

## Authentication Configuration

- `NEXTAUTH_SECRET` - Secret key for NextAuth.js (required for authentication)
- `NEXTAUTH_URL` - Base URL for NextAuth.js (default: `http://localhost:3000`)

## Example .env File

```bash
# LLM Provider Configuration
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=4096

# FakeStoreAPI Configuration
FAKE_STORE_BASE_URL=https://fakestoreapi.com
FAKE_STORE_TIMEOUT=15.0

# Database Configuration
DATABASE_URL=sqlite:///./shopping_assistant.db

# Vector Database Configuration
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Authentication
NEXTAUTH_SECRET=your-nextauth-secret-here
NEXTAUTH_URL=http://localhost:3000
```

## Usage Notes

1. **Required Variables**: At minimum, you need to set:
   - `LLM_PROVIDER` and the corresponding `{PROVIDER}_API_KEY`
   - `FAKE_STORE_BASE_URL` (if different from default)

2. **Optional Variables**: All other variables have sensible defaults and can be omitted unless you need to customize them.

3. **Switching Providers**: To switch LLM providers, simply change `LLM_PROVIDER` and set the corresponding API key. No code changes needed!

4. **Database**: The default SQLite database is fine for development. For production, use PostgreSQL by setting `DATABASE_URL`.

5. **Vector Database**: ChromaDB is the default and works out of the box. Qdrant support is planned for future releases.

## Environment Variable Loading

Environment variables are loaded in this order:
1. System environment variables
2. `.env` file in the project root
3. Default values (as specified above)

The `.env` file is automatically loaded by `python-dotenv` when the application starts.
