# ShopAI — E-Commerce Shopping Assistant

An AI-powered conversational shopping assistant built with **Next.js**, **FastAPI**, and **Claude AI**. Users can browse products, compare items, and manage a shopping cart entirely through natural language.

## Architecture

```
┌─────────────────┐     Streaming JSON     ┌──────────────────┐     REST      ┌──────────────────┐
│   Next.js 15    │ ◄──────────────────────►│   FastAPI        │ ◄────────────►│  Fake Store API  │
│   React 19      │     POST /chat          │   Claude Agent   │               │  fakestoreapi.com│
│   TailwindCSS   │                         │   Tool Execution │               │                  │
└─────────────────┘                         └──────────────────┘               └──────────────────┘
```

**Frontend** — Next.js 15 with TypeScript, TailwindCSS, streaming chat UI with rich product cards.

**Backend** — FastAPI with Claude AI (Anthropic SDK). The agent uses tool/function calling to search products, fetch details, and manage the cart. Responses stream back via Server-Sent Events.

**AI Agent** — Uses Claude's native tool calling with 6 tools: `search_products`, `get_product_details`, `add_to_cart`, `get_cart`, `remove_from_cart`, `update_cart_quantity`. Multi-turn conversation context is maintained per session.

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Anthropic API key

### 1. Clone and configure
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
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

- **Claude native tool calling** over LangChain — simpler, fewer dependencies, direct control over the agent loop
- **Streaming responses** — text chunks stream to the UI immediately while tool calls execute in the background, giving instant feedback
- **In-memory cart** — session-scoped cart stored server-side; sufficient for the assignment scope, easily swappable for a database
- **Rich rendering** — tool results (products, cart items) are sent as structured data to the frontend for card-based rendering, rather than relying on markdown alone
- **Minimal dependencies** — production-ready without unnecessary abstractions
