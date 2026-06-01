import os, uuid, logging
from typing import List, Dict, Optional
import chromadb
from config.settings import settings
from .embeddings import embed_texts, embed_query

logger = logging.getLogger(__name__)
COLL = "cbqa_v5"
_client = _collection = None

def _cli():
    global _client
    if _client is None:
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    return _client

def get_col():
    global _collection
    if _collection is None:
        _collection = _cli().get_or_create_collection(COLL, metadata={"hnsw:space":"cosine"})
    return _collection

def store_chunks(chunks: List[Dict]) -> int:
    if not chunks: return 0
    col = get_col()
    texts = [c["text"] for c in chunks]
    metas = [c["metadata"] for c in chunks]
    ids = [str(uuid.uuid4()) for _ in chunks]
    B = 128
    embs = []
    for i in range(0, len(texts), B):
        embs.extend(embed_texts(texts[i:i+B]))
        logger.info(f"Embedded {min(i+B,len(texts))}/{len(texts)}")
    for i in range(0, len(chunks), B):
        col.add(ids=ids[i:i+B], embeddings=embs[i:i+B], documents=texts[i:i+B], metadatas=metas[i:i+B])
    logger.info(f"Stored {len(chunks)} chunks. Total: {col.count()}")
    return len(chunks)

def retrieve_vector(query: str, top_k: int) -> List[Dict]:
    try:
        col = get_col(); n = col.count()
        if n == 0: return []
        res = col.query(query_embeddings=[embed_query(query)], n_results=min(top_k, n), include=["documents","metadatas","distances"])
        return [{"text":d,"metadata":m,"score":round(1-dist,4)} for d,m,dist in zip(res["documents"][0],res["metadatas"][0],res["distances"][0])]
    except Exception as e:
        logger.error(f"Vector retrieval error: {e}"); return []

def clear():
    global _collection
    try: _cli().delete_collection(COLL)
    except Exception: pass
    _collection = None; get_col()

def db_stats():
    try: return {"total_chunks": get_col().count(), "collection": COLL}
    except Exception: return {"total_chunks": 0, "collection": COLL}
