# CBQA V8 — Enterprise Architecture Blueprint

> **AI-Powered Repository Intelligence Platform**
> Primary LLM: Groq (Llama-3.3-70b) · Fallback: Gemini 2.5 Flash · Hybrid RAG: BM25 + FAISS Vector + HyDE + Cohere Rerank

---

## 1. System Context — C4 Level 1

High-level view of users, platform boundaries, and external integrations.

```mermaid
flowchart TB
    classDef person fill:#0ea5e9,stroke:#0284c7,stroke-width:2px,color:#fff,font-weight:bold
    classDef system fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff,font-weight:bold
    classDef external fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff
    classDef boundary fill:none,stroke:#334155,stroke-width:2px,stroke-dasharray:8 4

    User["👤 Developer"]

    subgraph Platform ["CBQA Platform"]
        direction TB
        CBQA["💻 CBQA Web Application"]
    end

    GitHub["🌐 GitHub API"]
    GroqLLM["🤖 Groq LLM — Primary"]
    GeminiLLM["🤖 Gemini — Fallback"]

    User -->|"HTTPS · REST API"| CBQA
    CBQA -->|"ZIP Download · Token Auth"| GitHub
    CBQA -->|"REST · API Key"| GroqLLM
    CBQA -.->|"Failover · API Key"| GeminiLLM

    class User person
    class CBQA system
    class GitHub,GroqLLM,GeminiLLM external
    class Platform boundary
```

---

## 2. Container Architecture — C4 Level 2

Running components, middleware boundaries, storage layers, and external connections.

```mermaid
flowchart TB
    classDef client fill:#0ea5e9,stroke:#0284c7,stroke-width:2px,color:#fff
    classDef server fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef storage fill:#a855f7,stroke:#7c3aed,stroke-width:2px,color:#fff
    classDef ext fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff
    classDef group fill:#0f172a,stroke:#1e293b,stroke-width:1px,color:#94a3b8

    subgraph Browser ["Client Browser"]
        SPA["SPA · HTML/CSS/JS"]
    end

    subgraph Backend ["FastAPI Backend — main.py"]
        Uvicorn["Uvicorn ASGI Server"]
        FastAPI["FastAPI Router — routes.py"]
        Settings["Settings Manager — settings.py"]
        Logger["Structured Logger"]
    end

    subgraph Storage ["Storage Layer"]
        FAISS[("FAISS Index — faiss_index.bin")]
        Meta[("Metadata — faiss_meta.pkl")]
        Repo[("Repo State — repo_meta.pkl")]
        MemCache[("In-Memory Cache — Max 200")]
    end

    subgraph External ["External Services"]
        Git["GitHub API"]
        Groq["Groq — Llama 3.3 70B"]
        Gemini["Gemini 2.5 Flash"]
    end

    SPA -->|"HTTP REST"| Uvicorn
    Uvicorn --> FastAPI
    FastAPI -.-> Settings
    FastAPI -.-> Logger
    FastAPI -->|"Read/Write"| FAISS
    FastAPI -->|"Read/Write"| Meta
    FastAPI -->|"Read/Write"| Repo
    FastAPI -->|"Read/Write"| MemCache
    FastAPI -->|"Clone via HTTPS"| Git
    FastAPI -->|"Completions"| Groq
    FastAPI -.->|"Fallback"| Gemini

    class SPA client
    class Uvicorn,FastAPI,Settings,Logger server
    class FAISS,Meta,Repo,MemCache storage
    class Git,Groq,Gemini ext
    class Browser,Backend,Storage,External group
```

---

## 3. Ingestion Pipeline — C4 Level 3

Write path: clone → walk → AST analysis → chunking → embedding → index storage.

```mermaid
flowchart TD
    classDef api fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef process fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#1c1917
    classDef store fill:#a855f7,stroke:#7c3aed,stroke-width:2px,color:#fff
    classDef group fill:#0f172a,stroke:#1e293b,stroke-width:1px,color:#94a3b8

    API["POST /analyze-repo"]

    subgraph Loader ["loader.py — Data Ingestion"]
        Clone["clone_repo — ZIP Download"]
        Local["read_local — Local Directory"]
        Walk["walk_codebase — File Scanner"]
    end

    subgraph Analyzer ["analyzer.py — AST Engine"]
        Analyze["analyze_repo — Coordinator"]
        Imports["Import Graph Builder"]
        Classes["Class Hierarchy Parser"]
        DirPurp["Directory Purpose Mapper"]
        Config["Config File Detector"]
        Auth["Auth Pattern Scanner"]
    end

    subgraph Chunker ["chunker.py — Semantic Partitioning"]
        ChunkRoute["chunk_file — Strategy Router"]
        PyAST["Python AST Chunker"]
        Regex["JS/TS/Go/Rust Regex Chunker"]
        TextSplit["Text Split Fallback"]
    end

    subgraph Embedder ["embeddings.py + vectorstore.py"]
        Embed["SentenceTransformer Encode"]
        Normalize["L2 Normalize Vectors"]
        FAISSAdd["FAISS IndexFlatIP Add"]
    end

    subgraph BM25 ["bm25_index.py — Lexical Index"]
        Tokenize["Regex Tokenizer"]
        IDF["IDF Calculator"]
    end

    subgraph Disk ["Persistent Storage"]
        FBin[("faiss_index.bin")]
        FMeta[("faiss_meta.pkl")]
        RMeta[("repo_meta.pkl")]
        RFiles[("repo_files.pkl")]
    end

    API --> Clone
    API --> Local
    Clone --> Walk
    Local --> Walk

    Walk --> Analyze
    Analyze --> Imports
    Analyze --> Classes
    Analyze --> DirPurp
    Analyze --> Config
    Analyze --> Auth

    Walk --> ChunkRoute
    ChunkRoute --> PyAST
    ChunkRoute --> Regex
    ChunkRoute --> TextSplit

    PyAST --> Embed
    Regex --> Embed
    TextSplit --> Embed
    Embed --> Normalize --> FAISSAdd

    PyAST --> Tokenize
    Regex --> Tokenize
    TextSplit --> Tokenize
    Tokenize --> IDF

    FAISSAdd --> FBin
    FAISSAdd --> FMeta
    Analyze --> RMeta
    Walk --> RFiles

    class API api
    class Clone,Local,Walk,Analyze,Imports,Classes,DirPurp,Config,Auth,ChunkRoute,PyAST,Regex,TextSplit,Embed,Normalize,FAISSAdd,Tokenize,IDF process
    class FBin,FMeta,RMeta,RFiles store
    class Loader,Analyzer,Chunker,Embedder,BM25,Disk group
```

---

## 4. Retrieval and Inference Pipeline — C4 Level 3

Read path: cache check → hybrid search → RRF fusion → rerank → prompt → LLM with failover.

```mermaid
flowchart TD
    classDef api fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef process fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#1c1917
    classDef store fill:#a855f7,stroke:#7c3aed,stroke-width:2px,color:#fff
    classDef llm fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff
    classDef group fill:#0f172a,stroke:#1e293b,stroke-width:1px,color:#94a3b8

    API["POST /ask"]

    subgraph Cache ["cache.py"]
        CacheCheck["Query Cache Lookup"]
    end

    subgraph Retriever ["hybrid_retriever.py"]
        Intent["Intent Classification"]
        HyDE["HyDE Query Expansion"]

        subgraph Dense ["Dense Vector Search"]
            EmbedQ["Embed Query Vector"]
            VSearch["FAISS Inner Product Search"]
        end

        subgraph Sparse ["Sparse Keyword Search"]
            BM25S["BM25 Term Scoring"]
        end

        RRF["Reciprocal Rank Fusion"]
        Diversity["File Diversity Filter"]
        Dedup["Content Deduplication"]
    end

    subgraph Ranking ["Cohere Reranking — Optional"]
        Rerank["Cross-Encoder Rerank"]
    end

    subgraph Prompt ["prompt_builder.py"]
        Build["Prompt Assembly"]
    end

    subgraph Inference ["llm_client.py — Failover Chain"]
        Router["Provider Router"]
        Groq["Groq API — Primary"]
        Gemini["Gemini API — Fallback"]
        Ollama["Ollama — Local Option"]
    end

    subgraph Data ["Datastores"]
        FIdx[("FAISS Index")]
        BIdx[("BM25 Token Registry")]
        RMeta[("Repo Metadata")]
    end

    API --> CacheCheck
    CacheCheck -->|"Cache Miss"| Intent
    CacheCheck -->|"Cache Hit"| API

    Intent --> HyDE
    HyDE --> EmbedQ
    Intent --> BM25S

    EmbedQ --> VSearch
    FIdx --> VSearch
    BIdx --> BM25S

    VSearch --> RRF
    BM25S --> RRF
    RRF --> Diversity --> Dedup
    Dedup --> Rerank

    Rerank --> Build
    RMeta --> Build

    Build --> Router
    Router --> Groq
    Groq -->|"On Failure"| Gemini
    Router -.->|"Local Config"| Ollama

    Groq --> API
    Gemini --> API
    Ollama --> API

    class API api
    class CacheCheck,Intent,HyDE,EmbedQ,VSearch,BM25S,RRF,Diversity,Dedup,Rerank,Build,Router process
    class Groq,Gemini,Ollama llm
    class FIdx,BIdx,RMeta store
    class Cache,Retriever,Dense,Sparse,Ranking,Prompt,Inference,Data group
```

---

## 5. End-to-End Query Sequence

Complete runtime trace of a `/ask` request through all system layers.

```mermaid
sequenceDiagram
    autonumber
    actor User as Browser Client
    participant API as Routes — routes.py
    participant Cache as QueryCache — cache.py
    participant Ret as Hybrid Retriever
    participant Embed as Embeddings — SentenceTransformer
    participant FAISS as Vector DB — FAISS
    participant BM25 as Keyword DB — BM25
    participant Rerank as Cohere Rerank API
    participant Prompt as PromptBuilder
    participant LLM as LLM Client

    User->>API: POST /ask with question and history
    Note over API: Pydantic validates question max 3000 chars

    API->>Cache: Lookup by question hash and top_k
    alt Cache Hit
        Cache-->>API: Return cached response
        API-->>User: HTTP 200 — Cached AskResponse
    else Cache Miss
        API->>Ret: get_context with question and top_k

        par Dense Vector Path
            Ret->>Embed: embed_query generates dense vector
            Embed-->>Ret: Return vector array
            Ret->>FAISS: Inner Product similarity search
            FAISS-->>Ret: Top K dense chunks with scores
        and Sparse Keyword Path
            Ret->>BM25: Term frequency scoring
            BM25-->>Ret: Top K lexical chunks with scores
        end

        Note over Ret: RRF merge then diversity then dedup

        alt Cohere Rerank Enabled
            Ret->>Rerank: Re-order by cross-encoder relevance
            Rerank-->>Ret: Reranked top chunks
        end

        Ret-->>API: Final context chunks

        API->>Prompt: Build prompt with context and metadata
        Note over Prompt: Inject history and AST structures
        Prompt-->>API: Structured messages array

        API->>LLM: call_llm with messages

        alt Groq Primary
            LLM->>LLM: POST to Groq REST API
            alt Groq Success
                LLM-->>API: Completion text
            else Groq Failure or Timeout
                Note over LLM: Auto-failover triggered
                LLM->>LLM: POST to Gemini API
                LLM-->>API: Gemini completion text
            end
        else Gemini Direct
            LLM->>LLM: Gemini API call
            LLM-->>API: Completion text
        else Local Ollama
            LLM->>LLM: Ollama local call
            LLM-->>API: Completion text
        end

        API->>Cache: Store response in cache
        API-->>User: HTTP 200 — AskResponse JSON
    end
```

---

## 6. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML/CSS/JS SPA | Single-page app with Mermaid rendering |
| **Backend** | FastAPI + Uvicorn | Async ASGI web server with CORS |
| **Primary LLM** | Groq — Llama 3.3 70B | Fast inference for Q&A completions |
| **Fallback LLM** | Gemini 2.5 Flash | Auto-failover on Groq failure |
| **Local LLM** | Ollama — Mistral | Optional offline inference |
| **Embeddings** | SentenceTransformer — all-MiniLM-L6-v2 | Dense vector encoding |
| **Vector DB** | FAISS IndexFlatIP | Cosine similarity search |
| **Keyword Search** | Custom BM25 | Exact identifier matching |
| **Reranking** | Cohere Rerank v3 | Optional cross-encoder precision |
| **AST Parsing** | Python ast module + regex | Code-aware chunking |
| **Deployment** | Render.com | Web service with persistent disk |

---

## 7. Directory Structure

```
CBQA3/
├── main.py                    # Application entry point — Uvicorn launcher
├── config/
│   └── settings.py            # Environment config loader with validation
├── backend/
│   ├── api/
│   │   └── routes.py          # FastAPI endpoints and frontend serving
│   ├── analyzer/
│   │   └── analyzer.py        # AST code analysis and repo intelligence
│   ├── ingestion/
│   │   ├── loader.py          # GitHub ZIP download and local file reader
│   │   └── chunker.py         # AST and regex-based semantic chunking
│   └── rag/
│       ├── embeddings.py      # SentenceTransformer model management
│       ├── vectorstore.py     # FAISS index CRUD with persistence
│       ├── bm25_index.py      # BM25 lexical keyword search
│       ├── hybrid_retriever.py # HyDE + RRF fusion + diversity + dedup
│       ├── prompt_builder.py  # Structured prompt assembly with repo context
│       ├── llm_client.py      # Groq primary + Gemini fallback + Ollama
│       ├── cache.py           # LRU query cache with hash-based lookup
│       └── summarizer.py      # Full repo intelligence briefing generator
├── frontend/
│   └── index.html             # Complete SPA with dark theme and Mermaid
├── render.yaml                # Render.com deployment config
├── Procfile                   # Process file for deployment
├── requirements.txt           # Python dependencies
└── ARCHITECTURE.md            # This document
```

---

## 8. Deployment Configuration

```yaml
# render.yaml
services:
  - type: web
    name: cbqa-service
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - LLM_PROVIDER: groq          # Primary LLM
      - FAISS_DIR: /data/faiss_db   # Persistent storage path
      # Secrets via Render Dashboard:
      # GROQ_API_KEY, GEMINI_API_KEY, COHERE_API_KEY, GITHUB_TOKEN
    disk:
      name: faiss-data
      mountPath: /data
      sizeGB: 1
```

---

## 9. API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health with LLM provider and index stats |
| `GET` | `/stats` | Quick index and cache statistics |
| `POST` | `/analyze-repo` | Ingest a GitHub repo or local directory |
| `POST` | `/ask` | Query the indexed codebase with hybrid RAG |
| `POST` | `/summarize` | Generate full repo intelligence briefing |
| `GET` | `/repo-structure` | Return analyzed repo metadata |
| `GET` | `/file-content?path=...` | Return content of a specific indexed file |
| `DELETE` | `/clear` | Wipe index, cache, and persisted state |
| `GET` | `/` | Serve the frontend SPA |

---

## 10. LLM Failover Strategy

```mermaid
flowchart LR
    classDef primary fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef fallback fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#1c1917
    classDef fail fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff
    classDef group fill:#0f172a,stroke:#1e293b,stroke-width:1px,color:#94a3b8

    subgraph Strategy ["LLM Failover Chain"]
        direction LR
        Request["Incoming Request"]
        Groq["Groq API"]
        Retry["Retry with Backoff"]
        Gemini["Gemini Fallback"]
        Error["Error Response"]
        Success["Return Completion"]
    end

    Request --> Groq
    Groq -->|"200 OK"| Success
    Groq -->|"429 Rate Limited"| Retry
    Groq -->|"5xx Server Error"| Retry
    Retry -->|"Max 3 Retries"| Gemini
    Groq -->|"Timeout or Connection Error"| Gemini
    Gemini -->|"200 OK"| Success
    Gemini -->|"Failure"| Error

    class Request,Success primary
    class Groq,Retry fallback
    class Gemini fallback
    class Error fail
    class Strategy group
```

**Retry Policy:**
- Rate limit (429): Wait using `Retry-After` header or exponential backoff (max 30s)
- Server errors (5xx): Linear backoff with 3 max retries
- Timeout: Configurable via `GROQ_TIMEOUT` (default 60s)
- Bad request (400/413): Fail immediately — no retry

---

*CBQA V8 — Production Release · Groq Primary · Gemini Fallback · Hybrid RAG Intelligence*
