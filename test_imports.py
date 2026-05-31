"""Run before starting the server: python test_imports.py"""
import sys
errors = []

def ti(p):
    try: __import__(p); print(f"  ✅  {p}")
    except Exception as e: print(f"  ❌  {p}  →  {e}"); errors.append(p)

print("\n── Import checks ──────────────────────────────────")
ti("config.settings")
ti("backend.ingestion.loader")
ti("backend.ingestion.chunker")
ti("backend.analyzer.analyzer")
ti("backend.rag.embeddings")
ti("backend.rag.vectorstore")
ti("backend.rag.bm25_index")
ti("backend.rag.hybrid_retriever")
ti("backend.rag.cache")
ti("backend.rag.prompt_builder")
ti("backend.rag.llm_client")
ti("backend.rag.summarizer")
ti("backend.api.routes")

if errors:
    print(f"\n❌  {len(errors)} import(s) failed. Fix before running.\n"); sys.exit(1)
else:
    print("\n✅  All imports OK. Run: python main.py\n")
