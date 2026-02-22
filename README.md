# Aisle — Advanced E-Commerce Shopping Assistant

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

## Quick Start

### Prerequisites
- **Node.js 20+**
- **Python 3.11+**
- An **LLM API key** (Anthropic, Google Gemini, or OpenAI)

### 1. Clone and configure environment
```bash
git clone <repo-url>
cd e-commerce-shopping-assignment
cp .env.example .env
```

Edit `.env` with your settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | One of: `anthropic`, `gemini`, `openai` |
| `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY` | Yes* | API key for the provider you chose |
| `NEXTAUTH_SECRET` | For auth | Random string for NextAuth.js sessions (e.g. `openssl rand -base64 32`) |
| `JWT_SECRET` | For auth | Secret for backend JWT (can use same value as `NEXTAUTH_SECRET`) |
| `NEXT_PUBLIC_API_URL` | Yes (frontend) | Backend URL, e.g. `http://localhost:8000` |
| `NEXTAUTH_URL` | For auth | Frontend URL, e.g. `http://localhost:3000` |

\* Only the key for your chosen `LLM_PROVIDER` is required. Other optional vars (database, vector DB, Redis) are documented in `.env.example`.

### 2. Start the backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. You can use the app as a guest or **Sign in** / **Register** (when `NEXTAUTH_SECRET` and `JWT_SECRET` are set) for a persisted cart.

### Docker (alternative)
```bash
# From repo root; ensure .env exists with at least LLM_PROVIDER and the matching API key
docker compose up --build
```

- **Backend**: http://localhost:8000 (SQLite data is stored in Docker volume `backend_data`)
- **Frontend**: http://localhost:3000

## Bonus Features (Assignment Checklist)

| Category       | Feature                                              | Status |
|----------------|------------------------------------------------------|--------|
| **Advanced AI** | RAG with product embeddings, multi-agent, semantic search | ✅ Multi-agent (Router, Search, Cart, Comparison, Recommendation). RAG/vector DB in backend (ChromaDB). Intent mapping (e.g. TV → electronics). |
| **Infrastructure** | User auth (NextAuth.js), DB-backed cart, Docker      | ✅ NextAuth.js (signin/register). Database-backed cart. Docker Compose + Dockerfiles. |
| **Real-time**  | SSE for live updates                                 | ✅ Chat streamed via SSE; title streams word-by-word; product list pops up after. |
| **Quality**    | Unit and integration tests                          | ⏳ Placeholder (pytest / npm test). |
| **UX Polish**  | Product image galleries, suggested prompts, quick actions | ✅ Suggested prompts and quick action buttons (e.g. "Show electronics", "Show me TVs", "View my cart"). Product cards with image + details. |

Intent handling: queries like "show me TV" or "televisions" map to **electronics** and match TV-like products (monitors, displays) so the assistant no longer says "no such data".

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
- **Anthropic Claude**: e.g. `claude-sonnet-4-20250514`
- **Google Gemini**: e.g. `gemini-1.5-flash` (API key from [Google AI Studio](https://aistudio.google.com/apikey))
- **OpenAI**: e.g. `gpt-4o`

Switch providers by setting `LLM_PROVIDER` and the corresponding `*_API_KEY` in `.env`.

## Testing

```bash
# Backend (when tests are added)
cd backend
pytest

# Frontend lint
cd frontend
npm run lint
```

## Docker Deployment

From the repository root:

```bash
docker compose up --build
```

| Service  | URL                  |
|----------|----------------------|
| Backend  | http://localhost:8000 |
| Frontend | http://localhost:3000 |

The backend stores SQLite data in the `backend_data` volume. Ensure `.env` contains at least `LLM_PROVIDER` and the matching API key; set `NEXTAUTH_SECRET` and `JWT_SECRET` if you want sign-in/register to work.


