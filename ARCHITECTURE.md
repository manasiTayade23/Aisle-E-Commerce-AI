# Architecture Documentation

## Overview

This e-commerce shopping assistant is built with a **LangGraph-based multi-agent architecture** that is **LLM-agnostic** and uses **RAG (Retrieval-Augmented Generation)** for advanced product search and recommendations.

## System Architecture

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

## Key Components

### 1. LLM Abstraction Layer (`backend/app/llm/`)

**Purpose**: Provides a unified interface for multiple LLM providers.

**Supported Providers**:
- **Anthropic Claude** (`anthropic_llm.py`)
- **Google Gemini** (`gemini_llm.py`)
- **OpenAI GPT** (`openai_llm.py`)

**Key Features**:
- Unified `BaseLLM` interface
- Streaming support for all providers
- Tool/function calling abstraction
- LLM-agnostic agent framework

**Usage**:
```python
from app.llm import create_llm

# Create LLM instance (provider from env or explicit)
llm = create_llm(provider="anthropic")  # or "gemini", "openai"
```

### 2. LangGraph Multi-Agent System (`backend/app/agents/`)

**Purpose**: Specialized agents for different shopping tasks.

**Agents**:

1. **RouterAgent** (`router_agent.py`)
   - Analyzes user intent
   - Routes to appropriate specialized agent

2. **SearchAgent** (`search_agent.py`)
   - Product discovery and search
   - Keyword, category, price filtering
   - Natural language query understanding

3. **CartAgent** (`cart_agent.py`)
   - Shopping cart management
   - Add/remove/update items
   - Cart totals and summaries

4. **ComparisonAgent** (`comparison_agent.py`)
   - Side-by-side product comparison
   - Feature analysis
   - Recommendation generation

5. **RecommendationAgent** (`recommendation_agent.py`)
   - Personalized recommendations using RAG
   - Semantic similarity search
   - Context-aware suggestions

**Workflow**:
```
User Message → Router → [Search/Cart/Comparison/Recommendation] → Response
```

### 3. RAG System (`backend/app/rag/`)

**Purpose**: Semantic product search using vector embeddings.

**Components**:

- **EmbeddingGenerator** (`embeddings.py`)
  - Uses Sentence Transformers
  - Generates product embeddings
  - Configurable model (default: `all-MiniLM-L6-v2`)

- **VectorStore** (`vector_store.py`)
  - ChromaDB implementation (default)
  - Qdrant support (planned)
  - Cosine similarity search

- **RAGRetriever** (`retriever.py`)
  - Initializes vector store with FakeStoreAPI products
  - Semantic search with top-k retrieval
  - Enriches results with full product details

**Flow**:
```
Product Data → Embeddings → Vector Store → Query Embedding → Similarity Search → Results
```

### 4. Database Layer (`backend/app/database/`)

**Purpose**: Persistent storage for carts, users, orders, and conversations.

**Models**:
- `User`: User accounts (linked to NextAuth)
- `CartItem`: Shopping cart items (persistent)
- `Order`: Order history
- `WishlistItem`: User wishlists
- `Conversation`: Chat history

**Database**: SQLite (default) or PostgreSQL (configurable)

### 5. Graph Orchestration (`backend/app/graph/`)

**Purpose**: LangGraph workflow that orchestrates agents.

**State Management**:
- `user_message`: Current user input
- `session_id`: Session identifier
- `messages`: Conversation history
- `response`: Generated response
- `tool_calls`: Tool execution results
- `agent`: Active agent name
- `next_agent`: Routing decision
- `rag_context`: RAG retrieval results

## Configuration

### Environment Variables

See `.env.example` for all configuration options:

**LLM Configuration**:
- `LLM_PROVIDER`: Provider choice (anthropic/gemini/openai)
- `{PROVIDER}_API_KEY`: API key for chosen provider
- `{PROVIDER}_MODEL`: Model name (optional)

**FakeStoreAPI**:
- `FAKE_STORE_BASE_URL`: Base URL (default: https://fakestoreapi.com)

**Database**:
- `DATABASE_URL`: Database connection string

**Vector Database**:
- `VECTOR_DB_TYPE`: chroma or qdrant
- `CHROMA_PERSIST_DIR`: ChromaDB persistence directory

**Embeddings**:
- `EMBEDDING_MODEL`: Sentence transformer model name

## Data Flow

### Chat Request Flow

1. **User sends message** → Frontend
2. **POST /chat** → Backend
3. **Router Agent** analyzes intent
4. **Specialized Agent** processes request:
   - **Search**: Uses search tools
   - **Cart**: Uses cart management tools
   - **Comparison**: Fetches multiple products
   - **Recommendation**: Uses RAG for semantic search
5. **Tool Execution**:
   - Tools call FakeStoreAPI
   - Results returned to agent
6. **Agent generates response** with tool results
7. **Streaming response** sent to frontend via SSE

### RAG Flow

1. **Product ingestion** (on first request):
   - Fetch all products from FakeStoreAPI
   - Generate embeddings
   - Store in vector database

2. **Query processing**:
   - User query → Embedding
   - Vector similarity search
   - Top-k products retrieved
   - Full product details fetched
   - Context provided to agent

## Advanced Features

### 1. Multi-Agent Architecture
- Specialized agents for different tasks
- Intelligent routing based on intent
- Parallel processing capabilities

### 2. RAG with Semantic Search
- Product embeddings for better search
- Vector similarity matching
- Context-aware recommendations

### 3. LLM Agnostic
- Switch providers via config
- Unified interface
- No code changes needed

### 4. Database Persistence
- Cart persistence across sessions
- User authentication support
- Order history
- Conversation logging

### 5. Streaming Responses
- Real-time updates via SSE
- Tool execution feedback
- Progressive response rendering

## Future Enhancements

- [ ] Qdrant vector database support
- [ ] User authentication integration
- [ ] Price alerts and notifications
- [ ] Advanced recommendation algorithms
- [ ] Multi-language support
- [ ] Voice interface
- [ ] Mobile app support
