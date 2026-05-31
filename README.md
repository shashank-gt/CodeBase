# CBQA — AI-Powered Codebase Intelligence Platform

CBQA is an AI-powered repository analysis and question-answering platform that helps developers understand any codebase faster. Simply connect a GitHub repository or local project, and CBQA analyzes the architecture, code structure, dependencies, APIs, and execution flow to provide accurate, context-aware answers.

## Key Features

* **AI-Powered Codebase Understanding**: Deep semantic analysis of code structure, logic, and context.
* **Dual-Engine High-Availability LLM**: Dual-engine architecture featuring Groq (`llama-3.3-70b-versatile`) and Gemini (`gemini-2.5-flash` via the modern `google-genai` SDK) with robust, automatic bidirectional failover backup mechanisms.
* **Hybrid Retrieval System**: Combines semantic vector database search (ChromaDB) and exact keyword search (BM25) for ultimate recall.
* **Repository Metadata Disk Cache**: Implements standard local JSON-based persistence to automatically recover repository analysis meta across server restarts.
* **Dynamic Connection Detection**: Automatically resolves the active backend host dynamically (`window.location.origin`) with local `file://` launcher fallbacks to run perfectly under any staging, cloud VPS, or local deployment port.
* **Smooth Progressive UI**: Progressive drag-scrolling chatbot text rendering for natural conversation pacing (eliminating page snaps) combined with clean typography.
* **Intelligent Query Expansion & Reranking**: Advanced RAG workflow using HyDE (Hypothetical Document Embeddings) and Cohere AI Reranking to deliver optimal context.
* **Interactive Repository Explorer**: Complete files viewer, dependency visualizer, and custom architectural flow mapping.

## How It Works

1. Repository files are loaded and analyzed.
2. Source code is intelligently chunked based on language structure.
3. Embeddings and search indexes are generated.
4. User questions are enhanced and matched against relevant code.
5. Retrieved context is ranked and organized.
6. The AI generates structured, repository-aware answers.

## Core Technologies

### Backend

* Python
* FastAPI
* ChromaDB
* BM25 Retrieval
* Sentence Transformers
* Google GenAI SDK (Gemini)
* Groq Cloud API
* Ollama (Local LLM capability)
* JSON Metadata Disk-Persistence Cache

### AI & Retrieval

* Hybrid Search (Vector + Keyword)
* Query Expansion (HyDE)
* Reciprocal Rank Fusion (RRF)
* Cohere AI Reranking
* Retrieval-Augmented Generation (RAG)

### Frontend

* Clean Vanilla CSS Sleek Design
* Interactive Repository Explorer & Source Code Viewer
* Progressive Smooth-Scrolling Chat Assistant
* Architecture & Flow Diagrams (Mermaid.js integration)

## Available Capabilities

* Explain project architecture
* Understand authentication flows
* Trace API endpoints
* Analyze dependencies and integrations
* Explore file relationships
* Summarize repositories
* Identify execution paths
* Answer repository-specific questions with source references

## API Endpoints

| Endpoint          | Method | Purpose                                |
| ----------------- | ------ | -------------------------------------- |
| `/analyze-repo`   | POST   | Analyze and index a repository         |
| `/ask`            | POST   | Ask questions about the codebase       |
| `/repo-structure` | GET    | View repository structure and metadata |
| `/file-content`   | GET    | View contents of a specific file       |
| `/summarize`      | POST   | Generate repository summaries          |
| `/stats`          | GET    | View indexing and cache statistics     |
| `/health`         | GET    | Service health & LLM status            |
| `/clear`          | DELETE | Clear indexed data and disk cache      |

## Use Cases

* Understanding unfamiliar codebases
* Faster developer onboarding
* Repository documentation assistance
* Architecture exploration
* Code review support
* Technical due diligence
* Developer productivity enhancement

CBQA transforms complex repositories into searchable, explainable knowledge, helping developers spend less time navigating code and more time building software.


## Author
Shashank H K