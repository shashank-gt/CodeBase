# CBQA — AI-Powered Codebase Intelligence Platform

CBQA is an AI-powered repository analysis and question-answering platform that helps developers understand any codebase faster. Simply connect a GitHub repository or local project, and CBQA analyzes the architecture, code structure, dependencies, APIs, and execution flow to provide accurate, context-aware answers.

## Key Features

* AI-powered codebase understanding
* GitHub repository and local project analysis
* Hybrid retrieval using semantic search and keyword search
* Intelligent query expansion for improved answer quality
* Optional AI reranking for higher retrieval accuracy
* Interactive repository explorer and architecture visualization
* Repository summarization and technical insights
* Multi-turn conversational codebase Q&A
* OpenAI and local LLM support

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
* OpenAI API
* Ollama

### AI & Retrieval

* Hybrid Search (Vector + Keyword)
* Query Expansion
* Reciprocal Rank Fusion (RRF)
* AI Reranking
* Retrieval-Augmented Generation (RAG)

### Frontend

* Interactive Repository Explorer
* Chat-Based Code Assistant
* Architecture & Flow Visualization

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

| Endpoint          | Purpose                                |
| ----------------- | -------------------------------------- |
| `/analyze-repo`   | Analyze and index a repository         |
| `/ask`            | Ask questions about the codebase       |
| `/repo-structure` | View repository structure and metadata |
| `/summarize`      | Generate repository summaries          |
| `/stats`          | View indexing and cache statistics     |
| `/health`         | Service health status                  |
| `/clear`          | Clear indexed data                     |

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