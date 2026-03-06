# 💡 LUMEN — AI-Powered Assistant

LUMEN is a production-grade conversational AI assistant built with **LangGraph**, **Streamlit**, and **GPT-4o**. It combines real-time web search, live stock data via MCP, and per-thread document RAG into a single polished chat interface with persistent conversation history.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Web Search** | Real-time DuckDuckGo search for up-to-date news and information |
| 📈 **Live Stock Prices** | Fetches live market data for any ticker via Alpha Vantage (MCP server) |
| 📄 **Document Chat (RAG)** | Upload a document and ask questions about its contents using FAISS vector search |
| 💬 **Persistent Memory** | Conversations are saved to SQLite and fully resumable across sessions |
| 🗂️ **Multi-format Documents** | Supports PDF, DOCX, DOC, TXT, CSV, and PPTX |
| 🧹 **Auto Cleanup** | Threads older than 7 days are automatically purged |
| 🎨 **Dark UI** | Custom dark theme with a polished sidebar and chat interface |

---

## 🏗️ Project Structure

```
lumen/
├── app.py                  # Entry point — session state, routing
├── config.py               # All constants, paths, model settings
├── requirements.txt
├── .env.example
│
├── core/                   # LangGraph internals
│   ├── graph.py            # Graph assembly, LLM init, MCP tools, chatbot instance
│   ├── nodes.py            # chat_node — system prompt + RAG injection
│   ├── state.py            # ChatState TypedDict
│   └── checkpointer.py     # Async SQLite checkpointer setup
│
├── rag/                    # Retrieval-Augmented Generation
│   ├── ingest.py           # Document loading, chunking, FAISS indexing
│   └── store.py            # In-memory per-thread retriever store
│
├── tools/                  # LangChain tools
│   ├── rag_tool.py         # @tool — queries the per-thread FAISS retriever
│   ├── search_tool.py      # DuckDuckGo web search
│   └── stock_mcp.py        # MCP server — Alpha Vantage stock price tool
│
├── db/
│   └── database_utils.py   # SQLite thread tracker, cleanup, delete
│
└── ui/
    ├── app.py → chat.py    # Main chat area rendering
    ├── sidebar.py          # Sidebar: new chat, document upload, conversation list
    ├── dialogs.py          # @st.dialog definitions (e.g. delete confirmation)
    ├── utils.py            # load_css, load_html, thread/session helpers
    └── assets/
        ├── style.css       # Dark theme stylesheet
        └── welcome.html    # Welcome screen capability cards
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/lumen.git
cd lumen
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-...
```

### 5. Run the app

```bash
# Recommended (avoids trampoline issues on Windows)
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🔧 Configuration

All tuneable settings live in `config.py` — no need to hunt through code:

```python
# LLM
LLM_MODEL        = "gpt-4o"
LLM_TEMPERATURE  = 0.7
EMBEDDING_MODEL  = "text-embedding-3-small"

# RAG
CHUNK_SIZE       = 1000
CHUNK_OVERLAP    = 200
RETRIEVER_K      = 4          # Top-k chunks returned per query

# UI / DB
MAX_SIDEBAR_THREADS = 10
THREAD_CLEANUP_DAYS = 7
```

---

## 🛠️ How It Works

### Agent Graph

LUMEN uses a **LangGraph** state machine with two nodes:

```
START → chat_node ⟷ tools → END
```

- **`chat_node`** — Calls GPT-4o with a dynamically built system prompt. If a document is loaded for the current thread, a RAG instruction is appended telling the LLM to call `rag_tool` before answering.
- **`tools`** — A `ToolNode` that routes to whichever tool the LLM requested: `rag_tool`, `search_tool`, or `stock_get_price`.

### Persistent Memory

Conversation history is stored in a **SQLite database** (`chatbot.db`) via LangGraph's `AsyncSqliteSaver` checkpointer. Each conversation is identified by a UUID thread ID. A separate `thread_tracker` table records creation timestamps for automatic cleanup.

### Document RAG

1. User uploads a file via the sidebar.
2. `ingest_document()` loads it with the appropriate LangChain loader, splits it into chunks, and builds a **FAISS** vector index using `text-embedding-3-small`.
3. The retriever is stored in memory keyed by `thread_id` — each conversation has its own isolated document.
4. When the user asks a question, `chat_node` detects the loaded document and instructs the LLM to call `rag_tool`, which queries the FAISS index and returns the top-k relevant chunks.

### Stock Prices via MCP

Stock price lookups use the **Model Context Protocol (MCP)**. `stock_mcp.py` runs as a local stdio MCP server powered by `FastMCP`, exposing a `stock_get_price` tool backed by the Alpha Vantage API. LangGraph connects to it at startup via `MultiServerMCPClient`.

---

## 📦 Supported Document Types

| Extension | Type |
|---|---|
| `.pdf` | PDF Document |
| `.docx` / `.doc` | Word Document |
| `.txt` | Plain Text |
| `.csv` | CSV File |
| `.pptx` | PowerPoint Presentation |

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI `text-embedding-3-small` |
| Agent Framework | LangGraph |
| Vector Store | FAISS |
| Web Search | DuckDuckGo (via `langchain-community`) |
| Stock Data | Alpha Vantage API |
| Tool Protocol | MCP (Model Context Protocol) |
| Frontend | Streamlit |
| Persistence | SQLite + LangGraph AsyncSqliteSaver |
| Document Loaders | LangChain Community |

---

## 📄 License

MIT License — feel free to use, modify and distribute.