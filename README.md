# CBQA — AI-Powered Codebase Intelligence Platform

CBQA is an AI-powered repository intelligence platform that enables developers to understand, explore, and interact with any codebase through natural language. By analyzing a GitHub repository or local project, CBQA provides deep insights into architecture, dependencies, execution flow, APIs, and code relationships, helping developers navigate complex projects with confidence.

---

# Key Features

* AI-powered repository understanding
* GitHub repository and local project analysis
* Hybrid retrieval using **FAISS** and **BM25**
* HyDE query expansion for improved retrieval quality
* Intelligent context selection and optional AI reranking
* Interactive repository explorer with file viewer
* Architecture, dependency, and class hierarchy visualization
* Repository summarization and technical insights
* Multi-turn conversational codebase Q&A
* Automatic repository persistence and recovery across server restarts
* Groq as the primary LLM with automatic Gemini fallback

---

# How It Works

1. Load and analyze a GitHub repository or local project.
2. Parse source code using language-aware chunking and repository analysis.
3. Generate embeddings and build FAISS and BM25 indexes.
4. Enhance user queries with intelligent retrieval techniques.
5. Retrieve, rank, and organize the most relevant repository context.
6. Generate repository-aware answers with architecture, execution flow, and source references.

---


# Core Technologies

### Backend

* Python
* FastAPI
* FAISS
* BM25 Retrieval
* Sentence Transformers
* Groq API
* Gemini API (Fallback)

### AI & Retrieval

* Retrieval-Augmented Generation (RAG)
* Hybrid Search (FAISS + BM25)
* HyDE Query Expansion
* Reciprocal Rank Fusion (RRF)
* Intelligent Context Selection
* AI Reranking

### Frontend

* HTML, CSS, JavaScript
* Interactive Repository Explorer
* Chat-Based Code Assistant
* Architecture & Dependency Visualization
* Dynamic File Viewer

---

# Capabilities

* Explain project architecture
* Understand execution flow
* Trace API endpoints
* Analyze dependencies and integrations
* Explore file and module relationships
* Visualize repository architecture and class hierarchy
* Summarize repositories and technical design
* Explain code with file references
* Answer repository-specific questions using contextual retrieval

---

# API Endpoints

| Endpoint          | Purpose                                        |
| ----------------- | ---------------------------------------------- |
| `/analyze-repo`   | Analyze and index a repository                 |
| `/ask`            | Ask questions about the repository             |
| `/repo-structure` | Retrieve repository structure and metadata     |
| `/summarize`      | Generate an AI-powered repository summary      |
| `/stats`          | View indexing, retrieval, and cache statistics |
| `/health`         | Check application and retrieval status         |
| `/clear`          | Clear indexed repository data                  |

---

# Use Cases

* Understanding unfamiliar codebases
* Faster developer onboarding
* Repository documentation assistance
* Software architecture exploration
* Code review and debugging
* Dependency and integration analysis
* Technical due diligence
* AI-assisted software maintenance
* Developer productivity enhancement

---

# Highlights

* Hybrid semantic and keyword retrieval for high-precision answers
* Deep repository analysis using AST-based parsing
* Cross-file reasoning and execution flow understanding
* Interactive architecture, dependency, and hierarchy visualizations
* Persistent indexing with automatic recovery after server restarts
* Optimized retrieval pipeline for lower latency and reduced token usage
* Production-ready architecture with robust error handling and failover support

---

CBQA transforms complex repositories into searchable, explainable knowledge, enabling developers to spend less time navigating code and more time building software.

## Author

**Shashank H K**