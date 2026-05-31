"""
BM25 keyword retrieval — handles exact function/variable name lookups
that semantic search misses. Combined with vector search for hybrid retrieval.
"""
import logging, math, re
from typing import List, Dict
from collections import Counter

logger = logging.getLogger(__name__)

_index: List[Dict] = []          # list of {text, metadata, tokens}
_idf: Dict[str, float] = {}
_avg_dl: float = 0.0

K1 = 1.5
B  = 0.75


def _tokenize(text: str) -> List[str]:
    return re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text.lower())


def build_index(chunks: List[Dict]) -> None:
    global _index, _idf, _avg_dl
    _index = []
    for c in chunks:
        tokens = _tokenize(c["text"])
        _index.append({"text": c["text"], "metadata": c["metadata"], "tokens": tokens, "tf": Counter(tokens)})

    # IDF
    N = len(_index)
    df: Dict[str, int] = {}
    for doc in _index:
        for tok in set(doc["tokens"]):
            df[tok] = df.get(tok, 0) + 1
    _idf = {tok: math.log((N - freq + 0.5) / (freq + 0.5) + 1) for tok, freq in df.items()}

    total = sum(len(d["tokens"]) for d in _index)
    _avg_dl = total / N if N > 0 else 1.0
    logger.info(f"BM25 index built: {N} documents")


def search(query: str, top_k: int = 10) -> List[Dict]:
    if not _index:
        return []
    q_tokens = _tokenize(query)
    scores: List[float] = []
    for doc in _index:
        dl = len(doc["tokens"])
        score = 0.0
        for tok in q_tokens:
            if tok not in doc["tf"]:
                continue
            tf = doc["tf"][tok]
            idf = _idf.get(tok, 0.0)
            numer = tf * (K1 + 1)
            denom = tf + K1 * (1 - B + B * dl / _avg_dl)
            score += idf * (numer / denom)
        scores.append(score)

    ranked = sorted(enumerate(scores), key=lambda x: -x[1])
    results = []
    for idx, score in ranked[:top_k]:
        if score > 0:
            results.append({"text": _index[idx]["text"], "metadata": _index[idx]["metadata"], "score": round(score, 4), "source": "bm25"})
    return results


def is_ready() -> bool:
    return len(_index) > 0
