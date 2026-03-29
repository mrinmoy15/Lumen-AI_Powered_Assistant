# LUMEN — AI-Powered Assistant

LUMEN is a production-grade conversational AI assistant built with **LangGraph**, **FastAPI**, and **Streamlit**. It combines real-time web search, live stock data via MCP, and per-thread document RAG into a single polished chat interface with persistent conversation history.

---

## Features

| Feature | Description |
|---|---|
| **Web Search** | Real-time DuckDuckGo search for up-to-date news and information |
| **Live Stock Prices** | Fetches live market data for any ticker via Alpha Vantage (MCP server) |
| **Document Chat (RAG)** | Upload a document and ask questions about its contents using Pinecone vector search |
| **Persistent Memory** | Conversations saved to PostgreSQL and fully resumable across sessions |
| **Multi-format Documents** | Supports PDF, DOCX, DOC, TXT, CSV, and PPTX |
| **Auto Cleanup** | Threads older than 7 days are automatically purged |
| **Dark UI** | Custom dark theme with a polished sidebar and chat interface |

---

## Architecture

LUMEN uses a **decoupled frontend/backend architecture**:

```
User → Firebase Hosting (.web.app URL)
         ↓
   Streamlit Frontend (Cloud Run)
         ↓  HTTP / SSE
   FastAPI Backend (Cloud Run)
         ↓
   LangGraph Agent (GPT-4o + Tools)
    ├── Pinecone (vector store)
    ├── PostgreSQL / Cloud SQL (conversation history)
    ├── DuckDuckGo (web search)
    └── Alpha Vantage MCP (stock prices)
```

### API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/threads` | List all conversation threads |
| `POST` | `/threads` | Register a new thread |
| `DELETE` | `/threads/{id}` | Delete a thread and all its data |
| `GET` | `/threads/{id}/messages` | Get conversation history |
| `POST` | `/threads/{id}/chat` | Send message — streams SSE response |
| `POST` | `/threads/{id}/documents` | Upload and ingest a document |
| `DELETE` | `/threads/{id}/documents` | Remove document from thread |

---

## Project Structure

```
lumen/
├── app.py                   # Streamlit frontend entry point
├── config.py                # All constants, paths, model settings
├── requirements.txt
├── Dockerfile               # Single image used for both backend and frontend
├── docker-compose.yml       # Local dev: postgres + backend + frontend
├── deploy.ps1               # Terraform import + apply + Firebase deploy
├── new_image_deploy.ps1     # Full: build + push + deploy
├── makefile
│
├── backend/                 # FastAPI application
│   ├── main.py              # App + lifespan startup
│   └── routers/
│       ├── threads.py       # Thread CRUD + message history
│       ├── chat.py          # SSE streaming chat endpoint
│       └── documents.py     # Document upload and removal
│
├── core/                    # LangGraph internals
│   ├── graph.py             # Graph assembly, LLM init, MCP tools
│   ├── nodes.py             # chat_node — system prompt + RAG injection
│   ├── state.py             # ChatState TypedDict
│   └── checkpointer.py      # Async PostgreSQL checkpointer
│
├── rag/                     # Retrieval-Augmented Generation
│   ├── ingest.py            # Document loading, chunking, Pinecone indexing
│   └── store.py             # Per-thread Pinecone retriever store
│
├── tools/                   # LangChain tools
│   ├── rag_tool.py          # Queries the per-thread Pinecone retriever
│   ├── search_tool.py       # DuckDuckGo web search
│   └── stock_mcp.py         # MCP server — Alpha Vantage stock price tool
│
├── db/
│   └── database_utils.py    # PostgreSQL thread tracker, cleanup, delete
│
├── ui/
│   ├── chat.py              # Main chat area rendering
│   ├── sidebar.py           # Sidebar: new chat, document upload, conversation list
│   ├── dialogs.py           # Delete confirmation dialog
│   ├── utils.py             # CSS/HTML loaders, thread/session helpers
│   └── assets/
│       ├── style.css        # Dark theme stylesheet
│       └── welcome.html     # Welcome screen capability cards
│
└── my-terraform/            # GCP infrastructure as code
    ├── main.tf
    ├── variables.tf
    └── terraform.tfvars     # Secret values — never committed to git
```

---

## Local Development (Docker Compose)

### Prerequisites

- Docker Desktop installed and running
- A [Pinecone](https://console.pinecone.io) account with an index created:
  - **Name**: `lumen-rag`, **Dimensions**: `1536`, **Metric**: `cosine`

### 1. Clone the repository

```bash
git clone https://github.com/mrinmoy15/Lumen-AI_Powered_Assistant.git
cd Lumen-AI_Powered_Assistant
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```env
# API Keys
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=lumen-rag
ALPHA_VANTAGE_API_KEY=...

# Database
POSTGRES_PASSWORD=lumen123
DATABASE_URL=postgresql://postgres:lumen123@localhost:5432/lumen

# Backend URL (used by Streamlit frontend)
BACKEND_URL=http://localhost:8000

# Makefile / deploy scripts
APP_VERSION=1.0.0
GCP_PROJECT_ID=your-gcp-project-id
GCP_PROJECT_NUMBER=your-gcp-project-number
GCP_REGION=us-central1
```

### 3. Build and run

```bash
make build
# or
docker compose up --build
```

This starts three containers:
- **postgres** — pgvector-enabled PostgreSQL on port `5432`
- **backend** — FastAPI on port `8000`
- **frontend** — Streamlit on port `8501`

Open `http://localhost:8501` in your browser.

### Other useful commands

```bash
make run      # start without rebuilding
make down     # stop all containers
make logs     # tail container logs
make clean    # remove local image
```

---

## Configuration

All tuneable settings live in `config.py`:

```python
# LLM
LLM_MODEL        = "gpt-4o"
LLM_TEMPERATURE  = 0.7
EMBEDDING_MODEL  = "text-embedding-3-small"

# RAG
CHUNK_SIZE       = 1000
CHUNK_OVERLAP    = 200
RETRIEVER_K      = 4        # Top-k chunks returned per query

# UI
MAX_SIDEBAR_THREADS = 10
THREAD_CLEANUP_DAYS = 7
```

---

## GCP Cloud Deployment

### Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) installed
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- [Firebase CLI](https://firebase.google.com/docs/cli) installed (`make firebase-install`)
- GCP project created
- Pinecone index created (see Local Development prerequisites)

### Infrastructure overview

Terraform provisions:
- **Artifact Registry** — Docker image repository
- **Cloud SQL (PostgreSQL 16)** — Conversation persistence
- **Secret Manager** — All API keys stored securely
- **Cloud Run (backend)** — FastAPI service
- **Cloud Run (frontend)** — Streamlit service (public URL printed after deploy)

### First-time deployment

```bash
# 1. Authenticate with GCP (one-time)
gcloud auth login
gcloud auth application-default login

# 2. Full deploy: build image, push to Artifact Registry, Terraform apply
make deploy-initial
```

The frontend Cloud Run URL is printed to the terminal after deploy completes.

### Deploy a new image (subsequent updates)

```bash
make deploy-image
```

This builds a new Docker image, pushes it to Artifact Registry, and runs `terraform apply` to update the Cloud Run services. Firebase Hosting is skipped (not needed for image updates).

### What the deploy scripts do

**`new_image_deploy.ps1`** (called by both make commands):
1. Authenticates Docker with Artifact Registry
2. Builds the Docker image
3. Pushes to Artifact Registry
4. Calls `deploy.ps1`

**`deploy.ps1`**:
1. Sets the active GCP project
2. Runs `terraform init`
3. Imports any pre-existing Cloud SQL / Cloud Run / Secrets into Terraform state
4. Runs `terraform apply`

### Cloud SQL connection

On Cloud Run, PostgreSQL is accessed via a Unix socket (no open ports needed):
```
postgresql://postgres:password@/lumen?host=/cloudsql/PROJECT:REGION:lumen-postgres
```
This is automatically set as a Secret Manager secret by Terraform.

---

## How It Works

### Agent Graph

LUMEN uses a **LangGraph** state machine with two nodes:

```
START → chat_node ⟷ tools → END
```

- **`chat_node`** — Calls GPT-4o with a dynamically built system prompt. If a document is loaded for the current thread, a RAG instruction is appended telling the LLM to call `rag_tool` before answering.
- **`tools`** — A `ToolNode` that routes to whichever tool the LLM requested: `rag_tool`, `search_tool`, or `stock_get_price`.

### Document RAG

1. User uploads a file via the sidebar — the frontend POSTs it to `/threads/{id}/documents`
2. The backend ingests it: loads with the appropriate LangChain loader, splits into chunks, and indexes into **Pinecone** under a namespace keyed by `thread_id`
3. Vectors persist in Pinecone across restarts — re-uploading the same thread replaces the namespace
4. When the user asks a question, `chat_node` detects the loaded document and instructs the LLM to call `rag_tool`, which queries Pinecone and returns the top-k relevant chunks

### Stock Prices via MCP

Stock price lookups use the **Model Context Protocol (MCP)**. `stock_mcp.py` runs as a subprocess inside the backend container via stdio transport, exposing a `stock_get_price` tool backed by the Alpha Vantage API.

---

## Supported Document Types

| Extension | Type |
|---|---|
| `.pdf` | PDF Document |
| `.docx` / `.doc` | Word Document |
| `.txt` | Plain Text |
| `.csv` | CSV File |
| `.pptx` | PowerPoint Presentation |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI `text-embedding-3-small` |
| Agent Framework | LangGraph |
| Vector Store | Pinecone |
| Web Search | DuckDuckGo (`ddgs`) |
| Stock Data | Alpha Vantage API via MCP |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Conversation Persistence | PostgreSQL via LangGraph `AsyncPostgresSaver` |
| Document Loaders | LangChain Community |
| Infrastructure | Terraform + GCP (Cloud Run, Cloud SQL, Artifact Registry, Secret Manager) |

---

## URL 
`https://lumen-frontend-e5s2hl52sa-uc.a.run.app/`

## License

MIT License — feel free to use, modify and distribute.
