import hashlib, logging
from collections import OrderedDict
from typing import Optional, Dict
from config.settings import settings

logger = logging.getLogger(__name__)

class QueryCache:
    def __init__(self, max_size=200):
        self._c: OrderedDict = OrderedDict()
        self._max = max_size

    def _k(self, q, k): return hashlib.sha256(f"{q.strip().lower()}::{k}".encode()).hexdigest()[:16]
    def get(self, q, k) -> Optional[Dict]:
        if not settings.CACHE_ENABLED: return None
        key = self._k(q, k)
        if key in self._c: self._c.move_to_end(key); return self._c[key]
        return None
    def set(self, q, k, v):
        if not settings.CACHE_ENABLED: return
        key = self._k(q, k); self._c[key] = v; self._c.move_to_end(key)
        if len(self._c) > self._max: self._c.popitem(last=False)
    def invalidate(self): self._c.clear()
    def size(self): return len(self._c)

query_cache = QueryCache(settings.CACHE_MAX_SIZE)
