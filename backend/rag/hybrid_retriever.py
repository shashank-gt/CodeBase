"""
Hybrid retrieval pipeline for CBQA V8 — Production Release.
1. Query intent classification (skip HyDE for simple lookups)
2. Query expansion via HyDE (code-aware, only for complex queries)
3. BM25 keyword search (raw query for exact identifier matches)
4. Vector semantic search (HyDE-expanded for semantic depth)
5. Reciprocal Rank Fusion (RRF) merge
6. File diversity enforcement (cross-file coverage)
7. Content deduplication (fuzzy matching)
8. Cohere reranking (optional precision filter)
"""
import logging
from typing import List, Dict, Optional
from config.settings import settings
from .vectorstore import retrieve_vector
from . import bm25_index as bm25

logger = logging.getLogger(__name__)

MAX_CHUNKS_PER_FILE = 3  # Force cross-file diversity


# ── Query intent classification ──────────────────────────────────────────────

def _is_simple_lookup(query: str) -> bool:
    """Detect if query is a simple identifier/name lookup that doesn't need HyDE."""
    q = query.strip().lower()
    # Very short queries are usually identifier lookups
    if len(q.split()) <= 3:
        return True
    # Questions starting with "what is" about a specific identifier
    if q.startswith(("where is ", "find ", "show me ", "what is the ")) and len(q.split()) <= 6:
        return True
    return False


# ── HyDE: Hypothetical Document Embedding ────────────────────────────────────

def _hyde_expand(query: str) -> str:
    """Generate a hypothetical code snippet/explanation for better semantic recall.
    Uses a focused prompt optimized for code retrieval."""
    if not settings.USE_HYDE:
        return query
    if _is_simple_lookup(query):
        logger.debug("HyDE skipped: simple lookup query")
        return query
    try:
        from .llm_client import call_llm
        messages = [
            {"role": "system", "content": (
                "You are a code retrieval assistant. Given a developer question about a codebase, "
                "write a SHORT hypothetical code snippet or technical explanation (3-5 lines max) "
                "that would answer the question. Include likely function names, variable names, "
                "class names, file paths, and technical terms from the actual source code. "
                "Be concrete and specific. Output ONLY the code/text — no explanations."
            )},
            {"role": "user", "content": query},
        ]
        hyp = call_llm(messages)
        # Combine original query with hypothetical for richer embedding
        expanded = f"{query}\n\n{hyp[:350]}"
        logger.debug("HyDE expansion applied")
        return expanded
    except Exception as e:
        logger.debug(f"HyDE failed, using raw query: {e}")
        return query


# ── Reciprocal Rank Fusion ────────────────────────────────────────────────────

def _rrf(results_lists: List[List[Dict]], k: int = 60) -> List[Dict]:
    """Merge multiple ranked lists using RRF scoring."""
    scores: Dict[str, float] = {}
    docs: Dict[str, Dict] = {}

    for result_list in results_lists:
        for rank, doc in enumerate(result_list):
            key = f"{doc['metadata'].get('file', '')}:{doc['metadata'].get('start_line', '')}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            if key not in docs:
                docs[key] = doc

    merged = [docs[k] for k in sorted(scores, key=lambda x: -scores[x])]
    # Normalize scores to 0-1
    if merged:
        max_s = max(scores.values())
        for doc in merged:
            key = f"{doc['metadata'].get('file', '')}:{doc['metadata'].get('start_line', '')}"
            doc["score"] = round(scores.get(key, 0) / max_s, 4)
    return merged


# ── Cohere Reranking ──────────────────────────────────────────────────────────

def _rerank(query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
    """Rerank using Cohere cross-encoder for higher precision."""
    if not settings.USE_RERANK or not settings.COHERE_API_KEY:
        return chunks[:top_k]
    try:
        import cohere
        co = cohere.Client(settings.COHERE_API_KEY)
        docs = [c["text"][:512] for c in chunks]
        response = co.rerank(model="rerank-english-v3.0", query=query, documents=docs, top_n=top_k)
        reranked = [chunks[r.index] for r in response.results]
        logger.debug(f"Cohere reranked {len(chunks)} → {len(reranked)}")
        return reranked
    except Exception as e:
        logger.warning(f"Reranking failed, using raw order: {e}")
        return chunks[:top_k]


# ── File diversity enforcement ────────────────────────────────────────────────

def _enforce_file_diversity(chunks: List[Dict], max_per_file: int = MAX_CHUNKS_PER_FILE) -> List[Dict]:
    """Cap chunks per file to force cross-file coverage."""
    file_counts: Dict[str, int] = {}
    diverse = []
    overflow = []
    for c in chunks:
        f = c["metadata"].get("file", "")
        count = file_counts.get(f, 0)
        if count < max_per_file:
            diverse.append(c)
            file_counts[f] = count + 1
        else:
            overflow.append(c)
    return diverse + overflow


# ── Content deduplication ─────────────────────────────────────────────────────

def _deduplicate(chunks: List[Dict]) -> List[Dict]:
    """Remove duplicate and near-duplicate chunks."""
    seen_keys = set()
    seen_content = set()
    deduped = []

    for c in chunks:
        # Exact position dedup
        pos_key = (c["metadata"].get("file", ""), c["metadata"].get("start_line", 0))
        if pos_key in seen_keys:
            continue
        seen_keys.add(pos_key)

        # Content similarity dedup (first 200 chars)
        content_key = c["text"][:200].strip()
        if content_key in seen_content:
            continue
        seen_content.add(content_key)

        deduped.append(c)

    return deduped


# ── Main retrieval entry point ────────────────────────────────────────────────

def get_context(query: str, top_k: Optional[int] = None) -> List[Dict]:
    """
    Full hybrid retrieval pipeline:
    Intent → HyDE → BM25 (raw) + Vector (expanded) → RRF → diversity → dedup → rerank
    """
    fetch_k = settings.TOP_K
    final_k = top_k or settings.RERANK_TOP_K

    # 1. Query expansion (HyDE) — used for vector search only
    expanded_query = _hyde_expand(query)

    # 2. BM25 keyword search — uses RAW query for exact identifier matches
    bm25_results = bm25.search(query, top_k=fetch_k) if bm25.is_ready() else []

    # 3. Vector semantic search — uses EXPANDED query for semantic depth
    vector_results = retrieve_vector(expanded_query, top_k=fetch_k)

    # 4. RRF fusion
    if bm25_results and vector_results:
        merged = _rrf([vector_results, bm25_results])
    elif vector_results:
        merged = vector_results
    elif bm25_results:
        merged = bm25_results
    else:
        return []

    # 5. File diversity enforcement
    diverse = _enforce_file_diversity(merged)

    # 6. Deduplicate
    deduped = _deduplicate(diverse)

    # 7. Rerank (Cohere if enabled, otherwise top-k slice)
    final = _rerank(query, deduped, final_k)

    logger.debug(
        f"Retrieval: bm25={len(bm25_results)} vector={len(vector_results)} "
        f"merged={len(merged)} diverse={len(diverse)} deduped={len(deduped)} final={len(final)}"
    )
    return final


# ── Context formatting ────────────────────────────────────────────────────────

def format_context(chunks: List[Dict], repo_meta: Optional[Dict] = None) -> str:
    """Format retrieved chunks into a structured context string for the LLM."""
    if not chunks:
        return "No relevant code found in the indexed codebase."

    # Group by file for coherent context
    by_file: Dict[str, List] = {}
    for c in chunks:
        f = c["metadata"].get("file", "unknown")
        by_file.setdefault(f, []).append(c)

    parts = []

    # Repo metadata block (compact)
    if repo_meta:
        meta_lines = []
        if repo_meta.get("description"):
            meta_lines.append(f"Project: {repo_meta['description']}")
        if repo_meta.get("tech_stack"):
            meta_lines.append(f"Tech: {', '.join(repo_meta['tech_stack'][:8])}")
        if repo_meta.get("entry_points"):
            meta_lines.append("Entry points: " + ", ".join(repo_meta["entry_points"][:4]))
        if repo_meta.get("design_patterns"):
            meta_lines.append("Patterns: " + ", ".join(repo_meta["design_patterns"][:4]))
        if meta_lines:
            parts.append("### Repository Context\n" + "\n".join(meta_lines))

    # File-grouped code chunks
    idx = 1
    for file, file_chunks in by_file.items():
        file_role = ""
        if repo_meta and repo_meta.get("key_files"):
            for kf in repo_meta["key_files"]:
                if kf["file"] == file:
                    file_role = f"  [{kf['reason']}]"
                    break

        chunk_parts = []
        for c in file_chunks:
            m = c["metadata"]
            line = m.get("start_line", "?")
            name = m.get("name", "")
            ctype = m.get("type", "")
            lang = m.get("language", "")
            score = c.get("score", 0)
            doc = m.get("docstring", "")

            # Build header
            hdr = f"[{idx}] {file}:{line}"
            if name and name not in ("block", "chunk_0", "unknown"):
                hdr += f"  ({ctype}: {name})"
            hdr += f"  relevance={score:.0%}"
            if doc:
                hdr += f"\n    # {doc[:150]}"

            chunk_parts.append(f"{hdr}\n```{lang}\n{c['text'].strip()}\n```")
            idx += 1

        parts.append(f"### {file}{file_role}\n" + "\n\n".join(chunk_parts))

    return "\n\n---\n\n".join(parts)
