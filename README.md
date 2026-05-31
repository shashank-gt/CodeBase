# CBQA – AI-Powered Codebase Intelligence Platform

CBQA is an intelligent codebase analysis and question-answering platform designed to help developers understand repositories quickly and efficiently. By connecting a GitHub repository or local project, users can explore project architecture, analyze dependencies, trace execution flows, and interact with the codebase through natural language conversations.

## Overview

Understanding a large codebase can be time-consuming, especially when onboarding to a new project. CBQA simplifies this process by combining advanced retrieval techniques with AI-powered reasoning to provide accurate, context-aware insights directly from the source code.

The platform indexes repository content, retrieves the most relevant code sections, and generates structured explanations that help developers navigate complex systems with ease.

## Key Features

* Repository analysis for GitHub and local projects
* AI-powered codebase question answering
* Hybrid search using semantic and keyword-based retrieval
* Intelligent query enhancement for improved context matching
* Interactive repository explorer and architecture visualization
* Automated repository summaries and technical insights
* Multi-turn conversational support
* Support for both cloud-based and local language models

## Core Technologies

### Backend

* Python
* FastAPI
* ChromaDB
* BM25 Retrieval
* Sentence Transformers

### AI & Retrieval

* Retrieval-Augmented Generation (RAG)
* Hybrid Search (Vector + Keyword Retrieval)
* Query Expansion
* Reciprocal Rank Fusion (RRF)
* AI-Based Result Reranking

### Language Models

* OpenAI Models
* Ollama (Local LLM Support)

## Capabilities

CBQA enables developers to:

* Understand overall project architecture
* Explore authentication and authorization workflows
* Trace API endpoints and request flows
* Analyze dependencies and integrations
* Discover relationships between files and modules
* Generate repository summaries
* Follow runtime execution paths
* Receive repository-specific answers with source references

## API Endpoints

| Endpoint          | Description                                |
| ----------------- | ------------------------------------------ |
| `/analyze-repo`   | Analyze and index a repository             |
| `/ask`            | Ask questions about the codebase           |
| `/repo-structure` | Retrieve repository metadata and structure |
| `/summarize`      | Generate an AI-powered repository summary  |
| `/stats`          | View indexing and cache statistics         |
| `/health`         | Check application status                   |
| `/clear`          | Clear indexed repository data              |

## Use Cases

* Developer onboarding
* Codebase exploration
* Architecture understanding
* Documentation assistance
* Code review and maintenance
* Technical due diligence
* Productivity enhancement for development teams

## Conclusion

CBQA transforms complex repositories into searchable, understandable knowledge. By combining intelligent retrieval with AI-powered reasoning, it enables developers to spend less time navigating code and more time building impactful software.

## Author

**Shashank H K**