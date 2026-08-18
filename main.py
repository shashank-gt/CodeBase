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
    if settings.LLM_PROVIDER == "groq":
        model = settings.GROQ_MODEL
        fallback = f"fallback: gemini/{settings.GEMINI_MODEL}" if settings.GEMINI_API_KEY else "no fallback"
    elif settings.LLM_PROVIDER == "gemini":
        model = settings.GEMINI_MODEL
        fallback = ""
    else:
        model = settings.LOCAL_LLM_MODEL
        fallback = ""

    provider_display = f"{settings.LLM_PROVIDER} / {model}"
    if fallback:
        provider_display += f"  ({fallback})"

    print(f"""
+------------------------------------------------------------------+
|   CBQA V8 — AI Repository Intelligence Platform (Production) |
+------------------------------------------------------------------+
|  LLM      : {provider_display:<52}|
|  Embed    : {settings.EMBEDDING_MODEL:<52}|
|  Retrieval: BM25 + Vector (hybrid){' + HyDE' if settings.USE_HYDE else '':<31}|
|  Rerank   : {'Cohere (enabled)' if settings.USE_RERANK else 'disabled':<52}|
|  Cache    : {'enabled' if settings.CACHE_ENABLED else 'disabled':<52}|
|  Server   : http://localhost:{settings.PORT:<44}|
+------------------------------------------------------------------+
    """)
    uvicorn.run("backend.api.routes:app", host=settings.HOST, port=settings.PORT,
                reload=False, log_level=settings.LOG_LEVEL.lower())
