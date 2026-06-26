"""
FastAPI routes for CBQA V7 — AI Repository Intelligence Platform.
Endpoints: /analyze-repo, /ask, /repo-structure, /summarize, /health, /clear, /file-content
Frontend served at root (/).
"""
import os, logging, traceback
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from config.settings import settings
from backend.ingestion.loader import clone_repo, read_local, walk_codebase
from backend.ingestion.chunker import chunk_codebase
from backend.analyzer.analyzer import analyze_repo
from backend.rag.vectorstore import store_chunks, clear, db_stats
from backend.rag.hybrid_retriever import get_context, format_context
from backend.rag.prompt_builder import build_prompt
from backend.rag.llm_client import call_llm, get_active_provider
from backend.rag.cache import query_cache
from backend.rag.summarizer import summarize_repo
from backend.rag import bm25_index

logger = logging.getLogger(__name__)

app = FastAPI(title="CBQA V7", description="AI Repository Intelligence Platform", version="7.0.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

os.makedirs(settings.REPO_TEMP_DIR, exist_ok=True)

# Frontend directory
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

_repo_files: List[Dict] = []
_repo_meta:  Dict = {}


def _save_persisted_state():
    meta_path = os.path.join(settings.CHROMA_DIR, "repo_meta.pkl")
    files_path = os.path.join(settings.CHROMA_DIR, "repo_files.pkl")
    try:
        import pickle
        with open(meta_path, "wb") as f:
            pickle.dump(_repo_meta, f)
        with open(files_path, "wb") as f:
            pickle.dump(_repo_files, f)
        logger.info("Persisted repo structure and files to disk.")
    except Exception as e:
        logger.error(f"Failed to persist repo structure: {e}")


def _clear_persisted_state():
    meta_path = os.path.join(settings.CHROMA_DIR, "repo_meta.pkl")
    files_path = os.path.join(settings.CHROMA_DIR, "repo_files.pkl")
    for p in (meta_path, files_path):
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    logger.info("Cleared persisted repo state from disk.")


@app.on_event("startup")
def startup_event():
    global _repo_files, _repo_meta
    meta_path = os.path.join(settings.CHROMA_DIR, "repo_meta.pkl")
    files_path = os.path.join(settings.CHROMA_DIR, "repo_files.pkl")
    if os.path.exists(meta_path) and os.path.exists(files_path):
        try:
            import pickle
            with open(meta_path, "rb") as f:
                _repo_meta = pickle.load(f)
            with open(files_path, "rb") as f:
                _repo_files = pickle.load(f)
            logger.info("Loaded persisted repository structure from disk.")
        except Exception as e:
            logger.error(f"Failed to load persisted repo structure: {e}")

    try:
        from backend.rag.vectorstore import get_index_and_meta
        _, metadata = get_index_and_meta()
        if metadata:
            bm25_index.build_index(metadata)
            logger.info(f"Rebuilt BM25 index from {len(metadata)} chunks on startup.")
    except Exception as e:
        logger.error(f"Failed to rebuild BM25 index on startup: {e}")


# ── Pydantic models ───────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    github_url: Optional[str] = None
    local_path: Optional[str] = None
    clear_existing: bool = True

    @field_validator("github_url")
    @classmethod
    def val_url(cls, v):
        if v and not v.strip().startswith("https://github.com"):
            raise ValueError("Must be a GitHub URL (https://github.com/...)")
        return v.strip() if v else v

    @field_validator("local_path")
    @classmethod
    def val_path(cls, v):
        if v:
            p = os.path.abspath(v.strip())
            if not os.path.isdir(p):
                raise ValueError(f"Not a valid directory: {p}")
        return v


class AnalyzeResponse(BaseModel):
    status: str
    files_processed: int
    chunks_stored: int
    repo_meta: Dict
    message: str


class AskRequest(BaseModel):
    question: str
    top_k: Optional[int] = None
    history: Optional[List[Dict]] = None

    @field_validator("question")
    @classmethod
    def val_q(cls, v):
        if not v or not v.strip():
            raise ValueError("question cannot be empty")
        if len(v) > 3000:
            raise ValueError("question too long (max 3000 chars)")
        return v.strip()


class AskResponse(BaseModel):
    answer: str
    sources: List[Dict]
    chunks_used: int
    cached: bool
    retrieval_method: str


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    llm_model: str
    embedding_model: str
    vector_db_chunks: int
    cache_size: int
    bm25_ready: bool
    hyde_enabled: bool
    rerank_enabled: bool


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    s = db_stats()
    active = get_active_provider()
    if settings.LLM_PROVIDER == "groq":
        model = settings.GROQ_MODEL
    elif settings.LLM_PROVIDER == "gemini":
        model = settings.GEMINI_MODEL
    else:
        model = settings.LOCAL_LLM_MODEL
    return HealthResponse(
        status="ok", version="7.0.0",
        llm_provider=active, llm_model=model,
        embedding_model=settings.EMBEDDING_MODEL,
        vector_db_chunks=s["total_chunks"],
        cache_size=query_cache.size(),
        bm25_ready=bm25_index.is_ready(),
        hyde_enabled=settings.USE_HYDE,
        rerank_enabled=settings.USE_RERANK,
    )


@app.get("/stats")
def stats():
    return {**db_stats(), "cache_size": query_cache.size(), "bm25_ready": bm25_index.is_ready()}


@app.post("/analyze-repo", response_model=AnalyzeResponse)
def analyze_repo_endpoint(req: AnalyzeRequest):
    global _repo_files, _repo_meta
    if not req.github_url and not req.local_path:
        raise HTTPException(400, "Provide github_url or local_path.")
    try:
        if req.github_url:
            name = req.github_url.rstrip("/").split("/")[-1].replace(".git", "")
            target = os.path.join(settings.REPO_TEMP_DIR, name)
            source = clone_repo(req.github_url, target)
        else:
            source = read_local(req.local_path)

        if req.clear_existing:
            clear()
            query_cache.invalidate()
            _clear_persisted_state()

        files = walk_codebase(source)
        if not files:
            raise HTTPException(400, "No code files found in the repository.")

        _repo_files = files
        _repo_meta = analyze_repo(source, files)

        chunks = chunk_codebase(files)
        stored = store_chunks(chunks)

        # Build BM25 index from same chunks
        bm25_index.build_index(chunks)
        
        _save_persisted_state()

        return AnalyzeResponse(
            status="success",
            files_processed=len(files),
            chunks_stored=stored,
            repo_meta=_repo_meta,
            message=f"Indexed {len(files)} files → {stored} chunks. BM25 + vector ready.",
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Analysis failed: {e}")


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    s = db_stats()
    if s["total_chunks"] == 0:
        raise HTTPException(400, "No codebase indexed. POST to /analyze-repo first.")

    top_k = req.top_k or settings.RERANK_TOP_K

    cached = query_cache.get(req.question, top_k)
    if cached:
        return AskResponse(**cached, cached=True)

    try:
        chunks = get_context(req.question, top_k=top_k)
        has_bm25 = any(c.get("source") == "bm25" for c in chunks)
        retrieval_method = "hybrid (BM25+vector)" if has_bm25 else "vector"
        if settings.USE_RERANK and settings.COHERE_API_KEY:
            retrieval_method += "+rerank"
        if settings.USE_HYDE:
            retrieval_method += "+HyDE"

        context_str = format_context(chunks, repo_meta=_repo_meta if _repo_meta else None)
        messages = build_prompt(req.question, context_str, history=req.history,
                                repo_meta=_repo_meta if _repo_meta else None)
        answer = call_llm(messages)

        sources = [{
            "file": c["metadata"].get("file", ""),
            "line": c["metadata"].get("start_line", ""),
            "name": c["metadata"].get("name", ""),
            "type": c["metadata"].get("type", ""),
            "score": c.get("score", 0),
            "text": c["text"][:400],
        } for c in chunks]

        result = {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
            "retrieval_method": retrieval_method,
        }
        query_cache.set(req.question, top_k, result)
        return AskResponse(**result, cached=False)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Query failed: {e}")


@app.get("/repo-structure")
def repo_structure():
    if not _repo_meta:
        raise HTTPException(400, "No repo analyzed yet.")
    return _repo_meta


@app.get("/file-content")
def file_content(path: str):
    """Return the content of a specific file from the indexed repository."""
    if not _repo_files:
        raise HTTPException(400, "No repo indexed. Analyze a repo first.")
    for f in _repo_files:
        if f["relative_path"] == path:
            return {
                "path": f["relative_path"],
                "extension": f["extension"],
                "content": f["content"],
                "lines": len(f["content"].splitlines()),
            }
    raise HTTPException(404, f"File not found: {path}")


@app.post("/summarize")
def summarize():
    if not _repo_files:
        raise HTTPException(400, "No repo indexed. Analyze a repo first.")
    try:
        return {"summary": summarize_repo(_repo_files)}
    except Exception as e:
        raise HTTPException(500, f"Summarization failed: {e}")


@app.delete("/clear")
def clear_index():
    clear()
    query_cache.invalidate()
    _clear_persisted_state()
    global _repo_files, _repo_meta
    _repo_files = []
    _repo_meta = {}
    return {"status": "cleared"}


# ── Frontend serving (MUST be last — catch-all) ──────────────────────────────

@app.get("/")
def serve_frontend():
    """Serve the frontend UI at the root URL."""
    index_path = os.path.join(_frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CBQA API is running. Frontend not found at ./frontend/index.html"}
