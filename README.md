# ShopAI — Advanced E-Commerce Shopping Assistant

An AI-powered conversational shopping assistant built with **Next.js**, **FastAPI**, **LangGraph**, and **RAG**. Features a **multi-agent architecture** that is **LLM-agnostic** (supports Anthropic Claude, Google Gemini, OpenAI GPT) and uses **semantic search** with vector embeddings for intelligent product discovery.

## 🚀 Key Features

- **🤖 Multi-Agent Architecture**: Specialized agents for search, cart management, comparison, and recommendations
- **🔍 RAG with Semantic Search**: Vector embeddings for intelligent product discovery
- **🌐 LLM Agnostic**: Switch between Anthropic, Gemini, or OpenAI with a single config change
- **💾 Database Persistence**: SQLite/PostgreSQL for cart, orders, and user data
- **🔐 Authentication Ready**: NextAuth.js integration support
- **📡 Real-time Streaming**: Server-Sent Events for live updates
- **🐳 Docker Support**: Containerized deployment

## Architecture

```
┌─────────────────┐     SSE Streaming     ┌──────────────────┐     REST      ┌──────────────────┐
│   Next.js 15    │ ◄────────────────────►│   FastAPI        │ ◄────────────►│  Fake Store API  │
│   React 19      │     POST /chat          │   LangGraph      │               │  fakestoreapi.com│
│   NextAuth.js   │                         │   Multi-Agent    │               │                  │
│   TailwindCSS   │                         │   RAG System     │               └──────────────────┘
└─────────────────┘                         │   Vector DB      │
                                            │   SQLite/Postgres│
                                            └──────────────────┘
```

**Frontend** — Next.js 15 with TypeScript, TailwindCSS, streaming chat UI with rich product cards, NextAuth.js for authentication.

**Backend** — FastAPI with LangGraph multi-agent system. Uses RAG with ChromaDB for semantic product search. Supports multiple LLM providers (Anthropic, Gemini, OpenAI). Database-backed cart persistence.

**AI Agents**:
- **Router Agent**: Routes requests to specialized agents
- **Search Agent**: Product discovery and search
- **Cart Agent**: Shopping cart management
- **Comparison Agent**: Side-by-side product comparison
- **Recommendation Agent**: Personalized recommendations using RAG

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- LLM API key (Anthropic, Gemini, or OpenAI)

### 1. Clone and configure
```bash
cp .env.example .env
# Edit .env and configure:
# - LLM_PROVIDER (anthropic, gemini, or openai)
# - {PROVIDER}_API_KEY (your API key)
# - FAKE_STORE_BASE_URL (default: https://fakestoreapi.com)
```

### 2. Start backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker (alternative)
```bash
# Set your API key in .env first
docker compose up --build
```

## Design Decisions

- **LangGraph multi-agent architecture** — specialized agents for different tasks, better separation of concerns
- **LLM-agnostic design** — unified interface allows switching providers without code changes
- **RAG with vector embeddings** — semantic search for better product discovery and recommendations
- **Database persistence** — SQLite/PostgreSQL for cart, orders, and user data (backward compatible with in-memory for anonymous users)
- **Streaming responses** — Server-Sent Events for real-time updates and tool execution feedback
- **Vector database** — ChromaDB for efficient similarity search (Qdrant support planned)
- **Modular architecture** — easy to extend with new agents, tools, or LLM providers

## Advanced Features

### Multi-Agent System
- **Router Agent**: Intelligently routes requests to specialized agents
- **Search Agent**: Natural language product search with filters
- **Cart Agent**: Persistent cart management
- **Comparison Agent**: Side-by-side product analysis
- **Recommendation Agent**: RAG-powered personalized suggestions

### RAG System
- Product embeddings using Sentence Transformers
- ChromaDB vector database for semantic search
- Context-aware recommendations
- Automatic product indexing from FakeStoreAPI

### LLM Provider Support
- **Anthropic Claude**: Claude Sonnet 4
- **Google Gemini**: Gemini 2.0 Flash
- **OpenAI**: GPT-4o

Switch providers by changing `LLM_PROVIDER` in `.env`.

## Testing

```bash
# Backend tests (coming soon)
cd backend
pytest

# Frontend tests (coming soon)
cd frontend
npm test
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up --build

# Services:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
```

## Documentation

- [Architecture Documentation](./ARCHITECTURE.md) - Detailed system architecture
- [API Documentation](http://localhost:8000/docs) - FastAPI Swagger UI (when running)
