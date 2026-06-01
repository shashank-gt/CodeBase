"""
Hybrid retrieval pipeline:
1. Query expansion via HyDE (optional)
2. BM25 keyword search
3. Vector semantic search
4. Reciprocal Rank Fusion (RRF) merge
5. Deduplication
6. Cohere reranking (optional)
"""
import logging
from typing import List, Dict, Optional
from config.settings import settings
from .vectorstore import retrieve_vector
from . import bm25_index as bm25

logger = logging.getLogger(__name__)


# ── HyDE: Hypothetical Document Embedding ────────────────────────────────────

def _hyde_expand(query: str) -> str:
    """Generate a hypothetical code snippet that would answer the query,
    then use that as an additional search query for better retrieval."""
    if not settings.USE_HYDE:
        return query
    try:
        from .llm_client import call_llm
        messages = [
            {"role": "system", "content": "You are a code assistant. Write a short hypothetical code snippet or explanation (2-4 lines) that would answer the following question about a codebase. Be concrete and technical."},
            {"role": "user", "content": query},
        ]
        hyp = call_llm(messages)
        expanded = f"{query}\n\n{hyp[:300]}"
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
            key = f"{doc['metadata'].get('file','')}:{doc['metadata'].get('start_line','')}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            if key not in docs:
                docs[key] = doc

    merged = [docs[k] for k in sorted(scores, key=lambda x: -scores[x])]
    # Normalize scores
    if merged:
        max_s = max(scores.values())
        for doc in merged:
            key = f"{doc['metadata'].get('file','')}:{doc['metadata'].get('start_line','')}"
            doc["score"] = round(scores.get(key, 0) / max_s, 4)
    return merged


# ── Cohere Reranking ──────────────────────────────────────────────────────────

def _rerank(query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
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


# ── Main retrieval entry point ────────────────────────────────────────────────

def get_context(query: str, top_k: Optional[int] = None) -> List[Dict]:
    """
    Full hybrid retrieval:
    HyDE expand → BM25 + Vector → RRF merge → dedup → rerank
    """
    fetch_k = settings.TOP_K
    final_k = top_k or settings.RERANK_TOP_K

    # 1. Query expansion (HyDE)
    expanded_query = _hyde_expand(query)

    # 2. BM25 keyword search
    bm25_results = bm25.search(expanded_query, top_k=fetch_k) if bm25.is_ready() else []

    # 3. Vector semantic search
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

    # 5. Deduplicate by (file, start_line)
    seen, deduped = set(), []
    for r in merged:
        key = (r["metadata"].get("file",""), r["metadata"].get("start_line", 0))
        if key not in seen:
            seen.add(key); deduped.append(r)

    # 6. Rerank (Cohere if enabled)
    final = _rerank(query, deduped, final_k)

    logger.debug(f"Hybrid retrieval: bm25={len(bm25_results)}, vector={len(vector_results)}, merged={len(deduped)}, final={len(final)}")
    return final


def format_context(chunks: List[Dict], repo_meta: Optional[Dict] = None) -> str:
    """Format retrieved chunks into a structured context string for the LLM.
    Note: repo_meta is accepted for API compatibility but NOT injected here
    because build_prompt already includes it in the repo_block to avoid duplication."""
    if not chunks:
        return "No relevant code found in the indexed codebase."

    by_file: Dict[str, List] = {}
    for c in chunks:
        f = c["metadata"].get("file", "unknown")
        by_file.setdefault(f, []).append(c)

    parts = []

    idx = 1
    for file, file_chunks in by_file.items():
        file_parts = []
        for c in file_chunks:
            m = c["metadata"]
            line, name, ctype = m.get("start_line","?"), m.get("name",""), m.get("type","")
            lang, score, doc = m.get("language",""), c.get("score",0), m.get("docstring","")
            hdr = f"[{idx}] {file}:{line}"
            if name and name not in ("block","chunk_0","unknown"):
                hdr += f"  ({ctype}: {name})"
            hdr += f"  relevance={score:.0%}"
            if doc:
                hdr += f"\n    # {doc[:150]}"
            file_parts.append(f"{hdr}\n```{lang}\n{c['text'].strip()}\n```")
            idx += 1
        parts.append(f"### {file}\n" + "\n\n".join(file_parts))

    return "\n\n---\n\n".join(parts)


