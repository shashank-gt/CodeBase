# CBQA — AI-Powered Codebase Intelligence Platform

> Understand any codebase in minutes. Groq-powered hybrid RAG with automatic Gemini failover and token-optimized context generation.

CBQA is an AI-powered repository intelligence platform that enables developers to understand, explore, and interact with any codebase through natural language. By analyzing a GitHub repository or local project, CBQA provides deep insights into architecture, dependencies, execution flow, APIs, and code relationships — helping developers navigate complex projects with confidence.

---

## Key Features

* **Groq-first LLM** with automatic Gemini failover on failure
* **Token-Optimized Pipeline** — focused context budgeting, deduplication, and chunk capping (45–60% token reduction)
* AI-powered repository understanding with cross-file reasoning
* GitHub repository and local project analysis
* Hybrid retrieval using **FAISS** vector search and **BM25** keyword search
* **HyDE** query expansion for improved semantic retrieval
* **Reciprocal Rank Fusion (RRF)** for optimal result merging
* Intelligent context selection and optional **Cohere** AI reranking
* Interactive repository explorer with file viewer
* Architecture, dependency, and class hierarchy visualization
* Repository summarization and technical intelligence briefings
* Multi-turn conversational codebase Q&A with history pruning
* Automatic repository persistence and recovery across restarts
* Production-ready error handling, retry logic, and rate-limit management

---

## How It Works

1. **Ingest** — Load and analyze a GitHub repository (ZIP download) or local project
2. **Parse** — AST-based chunking for Python, regex-based for JS/TS/Go/Rust/Java
3. **Index** — Generate embeddings via SentenceTransformer, build FAISS + BM25 indexes
4. **Retrieve** — Hybrid search with HyDE expansion, RRF fusion, diversity, dedup
5. **Rank** — Optional Cohere cross-encoder reranking for precision
6. **Generate** — Groq LLM produces architecture-aware answers with source citations

---

## ⚡ Token Optimization & Efficiency

CBQA features an active context optimization pipeline designed to minimize token usage, lower latency, and prevent LLM rate-limit (TPM/RPM) bottlenecks:

| Optimization Layer | Strategy | Benefit |
|-------------------|----------|---------|
| **Context Ceiling** | Capped at 5,000 input tokens for Groq | Prevents token inflation and ensures fast inference |
| **Output Token Budget** | Optimized `LLM_MAX_TOKENS=2048` | Cuts reserved completion budget by 50% without truncating diagrams |
| **Focused Retrieval** | `RERANK_TOP_K=6` and `TOP_K=12` | Delivers high-relevance code snippets with 25–35% fewer tokens |
| **Chunk Capping & Diversity** | Max 2 chunks per file, 1,000-char chunk limit | Eliminates redundant code blocks from the same source file |
| **Metadata Deduplication** | Single-pass injection of repo metadata | Avoids redundant system context duplication in prompts |
| **Conversation Pruning** | Retains last 4 turns & caps prior assistant text at 600 chars | Prevents multi-turn conversation token buildup |
| **Compact HyDE Expansion** | 2–3 line hypothetical snippets | Reduces expansion step overhead |
| **Lean Summarization** | Scans top 35 directories with 7-line previews | Reduces full-repo briefing token consumption by ~65% |

---

## Core Technologies

### Backend
* Python · FastAPI · Uvicorn ASGI
* FAISS (IndexFlatIP) — cosine similarity vector search
* BM25 — exact identifier and keyword matching
* SentenceTransformers (all-MiniLM-L6-v2) — dense embeddings
* Groq REST API (Llama 3.3 70B) — primary LLM
* Gemini API (2.5 Flash) — automatic fallback LLM

### AI & Retrieval
* Retrieval-Augmented Generation (RAG)
* Hybrid Search (FAISS + BM25 + RRF)
* HyDE — Hypothetical Document Embedding
* File Diversity Enforcement
* Content Deduplication (fuzzy matching)
* Optional Cohere Reranking

### Frontend
* HTML, CSS, JavaScript — single-page application
* Mermaid.js — architecture and dependency diagrams
* Interactive Repository Explorer with file tree
* Chat-Based Code Assistant with markdown rendering
* Dynamic File Viewer with syntax highlighting

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/analyze-repo` | Analyze and index a repository |
| `POST` | `/ask` | Ask questions about the codebase |
| `POST` | `/summarize` | Generate AI-powered repo intelligence briefing |
| `GET` | `/repo-structure` | Retrieve repository structure and metadata |
| `GET` | `/file-content` | Get content of a specific indexed file |
| `GET` | `/stats` | View index, retrieval, and cache statistics |
| `GET` | `/health` | Check application health and LLM provider status |
| `DELETE` | `/clear` | Clear indexed repository data and cache |
| `GET` | `/` | Serve the frontend SPA |

---

## Capabilities

* Explain project architecture with Mermaid diagrams
* Trace execution flow across files with source citations
* Analyze API endpoints and route handlers
* Map dependencies and external integrations
* Explore file and module relationships
* Visualize class hierarchies and import graphs
* Summarize repositories with senior-engineer-level insights
* Answer any codebase question using contextual hybrid retrieval

---

## Deployment

Configured for **Render.com** with persistent disk storage:

```bash
# Local development
pip install -r requirements.txt
python main.py

# Production (Render)
# Set environment variables via Render Dashboard:
# GROQ_API_KEY, GEMINI_API_KEY (optional), COHERE_API_KEY (optional)
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed system diagrams and technical reference.

---

## Highlights

* **Groq primary + Gemini fallback** — zero-downtime LLM inference with auto-failover
* **Token-optimized RAG** — 45–60% reduction in token consumption with focused context budgeting
* **Hybrid RAG pipeline** — BM25 keyword + FAISS vector + HyDE + RRF fusion
* **AST-aware chunking** — preserves function/class boundaries, not arbitrary text splits
* **Cross-file reasoning** — import chains, data flow, and architectural patterns
* **Production hardened** — retry with backoff, rate limit handling, token trimming
* **Persistent indexing** — survives server restarts with automatic recovery
* **Premium UI** — dark theme SPA with Mermaid diagrams, file explorer, source preview

---

CBQA transforms complex repositories into searchable, explainable knowledge — enabling developers to spend less time navigating code and more time building software.

## Author

**Shashank H K**