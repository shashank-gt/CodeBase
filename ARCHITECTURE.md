# CBQA Enterprise-Grade Software Architecture Blueprint (Detailed)

This document provides a highly detailed, enterprise-grade software architecture reference for the **CBQA (Codebase Q&A) Platform**. It exposes AST-level components, concrete package boundaries, data transformation steps, error mitigation paths, configuration states, and infrastructure routing protocols.

---

## 1. C4 Level 1: System Context Diagram
Illustrates the user boundaries, system endpoints, TLS encryption layer, and integrations with external version control and LLM services.

```mermaid
flowchart TB
    %% Style Definitions
    classDef person fill:#08427b,stroke:#073766,stroke-width:1.5px,color:#fff;
    classDef system fill:#1168bd,stroke:#0f5ca8,stroke-width:1.5px,color:#fff;
    classDef external fill:#7f8c8d,stroke:#687677,stroke-width:1.5px,color:#fff;
    classDef boundary fill:none,stroke:#bdc3c7,stroke-width:1px,stroke-dasharray: 5 5;
    classDef protocol fill:#f1f5f9,stroke:#64748b,stroke-width:1px,color:#334155,font-size:10px;

    User["👤 Developer / Client UI<br><br>Submits repository links, executes conversational queries, and explores parsed class/directory structures."]
    
    subgraph Boundary ["CBQA Platform Boundary"]
        CBQA["💻 CBQA Web Application Container<br><br>Coordinates static AST analysis, builds dense/sparse indices, manages query caching, and formats context prompts."]
    end

    GitHub["🌐 GitHub VCS API<br><br>Hosts codebase repositories; queried via HTTPS clone processes to build local RAG context."]
    
    LLMs["🤖 LLM Providers (Groq / Gemini / Ollama)<br><br>Executes completions for Q&A and generates hypothetical responses for HyDE embedding alignment."]

    %% Connections with Protocols
    User -->|HTTPS Requests<br>Port 443 / TLS 1.3| CBQA
    CBQA -->|Git CLI Clone / HTTP Get<br>Token Auth| GitHub
    CBQA -->|HTTPS REST JSON Calls<br>API Key Auth| LLMs

    class User person;
    class CBQA system;
    class GitHub,LLMs external;
    class Boundary boundary;
```

---

## 2. C4 Level 2: Container Diagram
Details the running components within the host environment. Exposes the static front-end server, CORS middleware boundaries, configuration parsers, log formatters, caching structures, and local storage formats.

```mermaid
flowchart TB
    %% Style Definitions
    classDef client fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0369a1;
    classDef web fill:#d1fae5,stroke:#059669,stroke-width:1.5px,color:#047857;
    classDef storage fill:#f3e8ff,stroke:#7c3aed,stroke-width:1.5px,color:#6d28d9;
    classDef ext fill:#f1f5f9,stroke:#64748b,stroke-width:1.5px,color:#334155;
    classDef sub fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,color:#475569;

    subgraph ClientContainer ["Client Browser Tier"]
        Browser["SPA UI App (HTML/CSS/JS)<br><br>Deconstructs API responses to render conversational chats, hierarchical file trees, and dynamic Mermaid dependency trees."]
    end

    subgraph ServerContainer ["FastAPI Backend Environment (main.py)"]
        Uvicorn["Uvicorn ASGI Web Server<br><br>Asynchronously processes TCP connections and manages request workers."]
        
        FastAPI["FastAPI Engine (routes.py)<br><br>Implements CORS middleware validation, JSON schema validation, and health/stats routers."]
        
        Settings["Settings Manager (settings.py)<br><br>Loads environment variables, overrides configurations via DotEnv, and performs type casting/validation."]
        
        LogFormatter["Log Handler<br><br>Formats process logs: '%(asctime)s  %(levelname)-8s  %(name)s  %(message)s'."]
    end

    subgraph StorageContainer ["Storage & Memory Tier"]
        SSD[("Persistent Storage (/data)<br><br>Persists binary FAISS index (faiss_index.bin), metadata pickle (faiss_meta.pkl), and codebase state (repo_meta.pkl / repo_files.pkl).")]
        
        MemCache[("In-Memory Store<br><br>Holds transient BM25 lexical arrays and Q&A caches (Max Size: 200).")]
    end

    subgraph ExternalAPIs ["External Endpoints"]
        GitHost["GitHub VCS API"]
        LLMInference["LLM Providers (Groq / Gemini)"]
    end

    %% Container Data Flows
    Browser -->|HTTP REST Requests| Uvicorn
    Uvicorn --> FastAPI
    FastAPI -.->|Validates Env/Types| Settings
    FastAPI -.->|Writes System Logs| LogFormatter
    
    FastAPI -->|Write/Read binary states| SSD
    FastAPI -->|Write/Read runtime tables| MemCache
    
    FastAPI -->|Clones over HTTPS| GitHost
    FastAPI -->|Completions over HTTPS| LLMInference

    class Browser client;
    class Uvicorn,FastAPI,Settings,LogFormatter web;
    class SSD,MemCache storage;
    class GitHost,LLMInference ext;
```

---

## 3. C4 Level 3: Component Diagram (Ingestion & AST Engine)
Deconstructs the write pipeline, showing how files are loaded, analyzed using Abstract Syntax Trees, partitioned into chunk matrices, and converted into dense/sparse indices.

```mermaid
flowchart TD
    %% Style Definitions
    classDef api fill:#d1fae5,stroke:#059669,stroke-width:1.5px,color:#047857;
    classDef component fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#92400e;
    classDef db fill:#f3e8ff,stroke:#7c3aed,stroke-width:1.5px,color:#6d28d9;
    classDef sub fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,color:#475569;

    Routes["FastAPI Route Handler<br>(api/routes.py)<br><br>Exposes '/analyze-repo' and validates github_url/local_path parameters."]

    subgraph LoaderLib ["loader.py (Data Ingestion)"]
        Clone["clone_repo(git_url, target)<br><br>Clones repository via subprocess Git CLI; injects GITHUB_TOKEN if present."]
        ReadLocal["read_local(path)<br><br>Reads local files path; validates directories."]
        Walk["walk_codebase(source)<br><br>Traverses source files, filtering out binaries, ignoring '__pycache__', '.git', etc."]
    end

    subgraph AnalyzerLib ["analyzer.py (AST Code Parsing)"]
        Analyze["analyze_repo(source, files)<br><br>Core AST coordinator; compiles structured repository metadata JSON."]
        ImportGraph["_build_import_graph(files)<br><br>Extracts code imports using regex mappings for Python and JS/TS dependencies."]
        ClassHier["_class_hierarchy(files)<br><br>Parses class declarations and base names to build inheritance trees."]
        DirPurp["_directory_purposes(files)<br><br>Infers directory roles based on layout conventions (e.g., api, models, utils)."]
        ConfigDet["_config_files(files)"]
        AuthDet["_auth_patterns(files)"]
        BuildDet["_build_info(files)"]
    end

    subgraph ChunkerLib ["chunker.py (Semantic Partitioning)"]
        Chunk["chunk_codebase(files)<br><br>Loops over files; skips files above settings.MAX_FILE_KB."]
        ChunkFile["chunk_file(file)<br><br>Segments text using CHUNK_SIZE (400 chars) / CHUNK_OVERLAP (80 chars)."]
    end

    subgraph EmbedderLib ["embeddings.py & vectorstore.py (Vector Assembly)"]
        StoreChunks["store_chunks(chunks)<br><br>Calculates embeddings and adds them to FAISS index."]
        EmbedTexts["embed_texts(texts)<br><br>Loads SentenceTransformer (all-MiniLM-L6-v2) to encode chunk texts."]
        Normalize["_normalize_vectors(embs)<br><br>Performs L2 norm normalization on raw vectors to prepare for Inner Product cosine similarity search."]
        FAISS_Add["IndexFlatIP.add()<br><br>Registers normalized vectors in FAISS index."]
    end

    subgraph BM25Lib ["bm25_index.py (Lexical Assembly)"]
        BuildBM25["build_index(chunks)<br><br>Generates lexicon index of terms."]
        Tokenize["_tokenize(text)<br><br>Tokenizes inputs using regex: '[a-zA-Z_][a-zA-Z0-9_]*'."]
        ComputeIDF["IDF Calculator<br><br>Computes Inverse Document Frequency (math.log((N - freq + 0.5) / (freq + 0.5) + 1))."]
    end

    subgraph SSDStores ["Persistent Storage Files"]
        FAISS_Bin[("faiss_index.bin")]
        FAISS_Meta[("faiss_meta.pkl")]
        RepoMeta[("repo_meta.pkl")]
        RepoFiles[("repo_files.pkl")]
    end

    %% Call Chains
    Routes -->|1. Clone/Read| LoaderLib
    LoaderLib -->|2. Walker| Walk
    Walk -->|3. AST Analysis| AnalyzerLib
    Walk -->|3. Text Chunking| ChunkerLib

    Analyze --> ImportGraph
    Analyze --> ClassHier
    Analyze --> DirPurp
    Analyze --> ConfigDet
    Analyze --> AuthDet
    Analyze --> BuildDet

    ImportGraph -->|4. Save AST| RepoMeta
    ClassHier -->|4. Save AST| RepoMeta
    DirPurp -->|4. Save AST| RepoMeta
    ConfigDet -->|4. Save AST| RepoMeta
    AuthDet -->|4. Save AST| RepoMeta
    BuildDet -->|4. Save AST| RepoMeta
    
    Walk -->|4. Save Content| RepoFiles

    Chunk --> ChunkFile
    ChunkFile -->|5. Convert to Vectors| StoreChunks
    StoreChunks --> EmbedTexts
    EmbedTexts --> Normalize
    Normalize --> FAISS_Add
    FAISS_Add -->|6. Write Vector DB| FAISS_Bin
    StoreChunks -->|6. Write Chunk Meta| FAISS_Meta

    ChunkFile -->|5. Convert to Tokens| BuildBM25
    BuildBM25 --> Tokenize --> ComputeIDF

    class Routes api;
    class Clone,ReadLocal,Walk,Analyze,ImportGraph,ClassHier,DirPurp,ConfigDet,AuthDet,BuildDet,Chunk,ChunkFile,StoreChunks,EmbedTexts,Normalize,FAISS_Add,BuildBM25,Tokenize,ComputeIDF component;
    class FAISS_Bin,FAISS_Meta,RepoMeta,RepoFiles db;
    class LoaderLib,AnalyzerLib,ChunkerLib,EmbedderLib,BM25Lib,SSDStores sub;
```

---

## 4. C4 Level 3: Component Diagram (Retrieval & Inference Engine)
Illustrates the read pipeline, cache verification, dense vector searches, lexical keyword scoring, RRF score fusion, Cohere reranking, context assembly, and fallback API completions.

```mermaid
flowchart TD
    %% Styling Definitions
    classDef api fill:#d1fae5,stroke:#059669,stroke-width:1.5px,color:#047857;
    classDef component fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#92400e;
    classDef db fill:#f3e8ff,stroke:#7c3aed,stroke-width:1.5px,color:#6d28d9;
    classDef model fill:#fce7f3,stroke:#db2777,stroke-width:1.5px,color:#be185d;
    classDef sub fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,color:#475569;

    Routes["FastAPI Route Handler<br>(api/routes.py)<br><br>Exposes '/ask' and validates AskRequest inputs (max 3000 chars)."]

    subgraph CachingLib ["cache.py (Response Caching)"]
        Cache["Query Cache Manager<br><br>Checks cache status; maps queries to answers based on question & top_k."]
    end

    subgraph RetrieverLib ["hybrid_retriever.py (Hybrid Search)"]
        GetContext["get_context(query, top_k)<br><br>Executes parallel search and performs Reciprocal Rank Fusion (RRF)."]
        
        subgraph DenseSearch ["Dense Vector Retrieval"]
            EmbedQuery["embeddings.embed_query(query)<br><br>Generates dense vector representation of the query."]
            FAISS_Search["vectorstore.retrieve_vector(query, k)<br><br>Executes Inner Product similarity search in FAISS index."]
        end

        subgraph SparseSearch ["Sparse Lexical Retrieval"]
            BM25_Search["bm25_index.search(query, k)<br><br>Calculates BM25 keyword match score for chunks."]
        end
    end

    subgraph PromptLib ["prompt_builder.py & cohere (Formatting)"]
        Rerank["Cohere Rerank API<br><br>Optionally re-orders context chunks based on cross-encoder relevancy scores."]
        PromptBuilder["Prompt Builder<br><br>Synthesizes system commands, user question, active chat history, and AST repository metadata."]
    end

    subgraph InferenceLib ["llm_client.py (Inference Clients)"]
        CallLLM["call_llm(messages)<br><br>Routes prompt completions and handles provider failure states."]
        
        subgraph Providers ["Inference APIs"]
            Groq["Groq Client API<br>(Llama-3.3-70b-versatile)"]
            Gemini["Gemini API Fallback<br>(gemini-2.5-flash)"]
            Ollama["Ollama Local Client<br>(Mistral)"]
        end
    end

    subgraph DBStores ["Datastores (SSD & Memory)"]
        FAISS_Bin[("faiss_index.bin")]
        BM25_Idx[("BM25 Token Registry")]
        RepoMeta[("repo_meta.pkl")]
    end

    %% Call Sequences
    Routes -->|1. Lookup Cache| Cache
    Cache -->|2. Cache Miss| RetrieverLib
    
    GetContext --> EmbedQuery
    GetContext --> BM25_Search
    EmbedQuery -->|3. Search Vectors| FAISS_Search
    FAISS_Bin --> FAISS_Search
    BM25_Idx --> BM25_Search

    FAISS_Search -->|4. Dense Chunks| GetContext
    BM25_Search -->|4. Sparse Chunks| GetContext

    GetContext -->|5. Merge Chunks| Rerank
    Rerank -->|6. Top Context| PromptBuilder
    RepoMeta -->|6. Inject AST map| PromptBuilder

    PromptBuilder -->|7. Complete Prompt| CallLLM
    CallLLM -->|8. Request Inference| Groq
    Groq -->|9. On Error / Timeout| Gemini
    CallLLM -.->|Optional Local Config| Ollama
    
    Groq -->|10. Text Completion| Routes
    Gemini -->|10. Text Completion| Routes
    Ollama -->|10. Text Completion| Routes

    class Routes api;
    class Cache,GetContext,EmbedQuery,FAISS_Search,BM25_Search,Rerank,PromptBuilder component;
    class FAISS_Bin,BM25_Idx,RepoMeta db;
    class CallLLM,Groq,Gemini,Ollama model;
    class CachingLib,RetrieverLib,PromptLib,InferenceLib,DBStores sub;
```

---

## 5. End-to-End Sequence Diagram (Detailed Runtime Execution)
Traces the execution flow of a user query through the system, including validation rules, caching layer lookups, hybrid dense/sparse search, RRF score fusion, prompt compilation, and fallback inference routing.

```mermaid
sequenceDiagram
    autonumber
    actor User as Client UI (Browser)
    participant API as Routes (routes.py)
    participant Cache as QueryCache (cache.py)
    participant Ret as Hybrid Retriever (hybrid_retriever.py)
    participant Embed as Embeddings (embeddings.py)
    participant FAISS as Vector DB (vectorstore.py)
    participant BM25 as Keyword DB (bm25_index.py)
    participant Rerank as Cohere API
    participant Prompt as PromptBuilder (prompt_builder.py)
    participant LLM as LLM Client (llm_client.py)

    User->>API: POST /ask (question, top_k, history)
    
    Note over API: Pydantic Validation: Question length must be < 3000 chars
    
    API->>Cache: query_cache.get(question, top_k)
    
    alt Cache Hit (CACHE_ENABLED = true)
        Cache-->>API: Return cached AskResponse dictionary
        API-->>User: Return HTTP 200 (Cached Response)
    else Cache Miss / Invalidated Cache
        API->>Ret: get_context(question, top_k)
        
        par Dense Vector Retrieval
            Ret->>Embed: embeddings.embed_query(question)
            Embed-->>Ret: Return dense vector array
            Ret->>FAISS: retrieve_vector(dense_vector, top_k)
            Note over FAISS: L2 Norm vector normalization & FAISS Inner Product search
            FAISS-->>Ret: Return top K dense text chunks with cosine similarity score
        and Sparse Keyword Retrieval
            Ret->>BM25: search(question, top_k)
            Note over BM25: Tokenizes query and calculates BM25 term scores
            BM25-->>Ret: Return top K lexical chunks with BM25 score
        end
        
        Ret->>Ret: Merge chunks & calculate Reciprocal Rank Fusion (RRF)
        
        alt USE_RERANK = true & COHERE_API_KEY is configured
            Ret->>Rerank: Rerank combined context chunks
            Rerank-->>Ret: Return re-ordered top context chunks
        end
        
        Ret-->>API: Return final list of context chunks
        
        API->>Prompt: build_prompt(question, context, history, repo_meta)
        Note over Prompt: Injects conversation history (max last 14 messages) & AST structures
        Prompt-->>API: Return system/user structured messages array
        
        API->>LLM: call_llm(messages)
        
        activate LLM
        alt LLM_PROVIDER = "groq"
            LLM->>LLM: Call Groq chat completion API (Llama-3.3-70b)
            alt Groq Success
                LLM-->>API: Return completion text
            else Groq API Fail / Timeout
                Note over LLM: Groq Error Intercepted; triggering failover fallback
                LLM->>LLM: Call Gemini Completion API (Gemini-2.5-Flash)
                LLM-->>API: Return Gemini completion text
            end
        else LLM_PROVIDER = "gemini"
            LLM->>LLM: Call Gemini API (Gemini-2.5-Flash)
            LLM-->>API: Return Gemini completion text
        else LLM_PROVIDER = "local"
            LLM->>LLM: Call Ollama API (Mistral)
            LLM-->>API: Return Ollama completion text
        end
        deactivate LLM
        
        API->>API: Format citations & match line references
        API->>Cache: query_cache.set(question, top_k, response)
        API-->>User: Return HTTP 200 (AskResponse JSON)
    end
```
