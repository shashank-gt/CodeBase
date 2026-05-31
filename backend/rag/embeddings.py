import logging
from typing import List
from sentence_transformers import SentenceTransformer
from config.settings import settings

logger = logging.getLogger(__name__)
_model = None

def get_model():
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed_texts(texts: List[str]) -> List[List[float]]:
    return get_model().encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

def embed_query(q: str) -> List[float]:
    return embed_texts([q])[0]
