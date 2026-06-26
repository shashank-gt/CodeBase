import os, logging, pickle
from typing import List, Dict, Optional
import numpy as np
import faiss
from config.settings import settings
from .embeddings import embed_texts, embed_query

logger = logging.getLogger(__name__)

# Files for FAISS index and metadata persistence
INDEX_FILE = os.path.join(settings.CHROMA_DIR, "faiss_index.bin")
META_FILE = os.path.join(settings.CHROMA_DIR, "faiss_meta.pkl")

# In-memory caches for fast access
_index: Optional[faiss.IndexFlatIP] = None
_metadata: List[Dict] = []

def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors to unit length for Cosine Similarity via Inner Product."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)  # Avoid division by zero
    return vectors / norms

def get_index_and_meta():
    global _index, _metadata
    if _index is None:
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
            try:
                _index = faiss.read_index(INDEX_FILE)
                with open(META_FILE, "rb") as f:
                    _metadata = pickle.load(f)
                logger.info(f"Loaded FAISS index with {_index.ntotal} vectors from disk.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}. Reinitializing.")
                _index = None
                _metadata = []
        
        if _index is None:
            # Dynamically determine dimensions from a sample embedding query
            try:
                test_emb = embed_query("test")
                dim = len(test_emb)
            except Exception as e:
                logger.error(f"Failed to compute test embedding to get dimension: {e}. Falling back to 384.")
                dim = 384
            # We use IndexFlatIP (Inner Product) for cosine similarity on normalized vectors
            _index = faiss.IndexFlatIP(dim)
            _metadata = []
    return _index, _metadata

def store_chunks(chunks: List[Dict]) -> int:
    if not chunks:
        return 0
    
    index, metadata = get_index_and_meta()
    
    texts = [c["text"] for c in chunks]
    metas = [c["metadata"] for c in chunks]
    
    # 1. Compute embeddings
    logger.info(f"Computing embeddings for {len(chunks)} chunks...")
    embs_list = embed_texts(texts)
    embs = np.array(embs_list, dtype=np.float32)
    
    # 2. Normalize for Cosine Similarity
    embs_norm = _normalize_vectors(embs)
    
    # 3. Add to FAISS index
    index.add(embs_norm)
    
    # 4. Save metadata
    for text, meta in zip(texts, metas):
        metadata.append({"text": text, "metadata": meta})
        
    # 5. Persist to disk
    try:
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        faiss.write_index(index, INDEX_FILE)
        with open(META_FILE, "wb") as f:
            pickle.dump(metadata, f)
        logger.info(f"Stored {len(chunks)} chunks in FAISS index. Total count: {index.ntotal}")
    except Exception as e:
        logger.error(f"Failed to persist FAISS index: {e}")
        
    return len(chunks)

def retrieve_vector(query: str, top_k: int) -> List[Dict]:
    try:
        index, metadata = get_index_and_meta()
        n = index.ntotal
        if n == 0:
            return []
        
        # 1. Embed query
        q_emb_list = embed_query(query)
        q_emb = np.array([q_emb_list], dtype=np.float32)
        q_emb_norm = _normalize_vectors(q_emb)
        
        # 2. Query index
        k = min(top_k, n)
        distances, indices = index.search(q_emb_norm, k)
        
        # 3. Format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            item = metadata[idx]
            # FAISS IndexFlatIP returns Cosine Similarity directly since vectors are normalized!
            score = round(float(dist), 4)
            results.append({
                "text": item["text"],
                "metadata": item["metadata"],
                "score": score
            })
        return results
    except Exception as e:
        logger.error(f"FAISS vector retrieval error: {e}")
        return []

def clear():
    global _index, _metadata
    _index = None
    _metadata = []
    if os.path.exists(INDEX_FILE):
        try:
            os.remove(INDEX_FILE)
        except Exception:
            pass
    if os.path.exists(META_FILE):
        try:
            os.remove(META_FILE)
        except Exception:
            pass
    logger.info("Cleared FAISS index and metadata.")
    get_index_and_meta()

def db_stats():
    try:
        index, _ = get_index_and_meta()
        return {"total_chunks": index.ntotal, "collection": "faiss_index"}
    except Exception:
        return {"total_chunks": 0, "collection": "faiss_index"}
