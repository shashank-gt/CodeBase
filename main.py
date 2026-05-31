import sys, os, logging
import uvicorn
from config.settings import settings

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

from backend.api.routes import app  # noqa: E402

if __name__ == "__main__":
    if settings.LLM_PROVIDER == "gemini":
        model = settings.GEMINI_MODEL
    elif settings.LLM_PROVIDER == "openai":
        model = settings.OPENAI_MODEL
    else:
        model = settings.LOCAL_LLM_MODEL

    print(f"""
+------------------------------------------------------------------+
|       CBQA - AI Repository Intelligence Platform  V6.0           |
+------------------------------------------------------------------+
|  LLM      : {settings.LLM_PROVIDER} / {model:<47}|
|  Embed    : {settings.EMBEDDING_MODEL:<52}|
|  Retrieval: BM25 + Vector (hybrid){' + HyDE' if settings.USE_HYDE else '':<31}|
|  Rerank   : {'Cohere (enabled)' if settings.USE_RERANK else 'disabled':<52}|
|  Cache    : {'enabled' if settings.CACHE_ENABLED else 'disabled':<52}|
|  Server   : http://localhost:{settings.PORT:<44}|
+------------------------------------------------------------------+
    """)
    uvicorn.run("backend.api.routes:app", host=settings.HOST, port=settings.PORT,
                reload=False, log_level=settings.LOG_LEVEL.lower())
