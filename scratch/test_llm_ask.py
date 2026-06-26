import os
import sys

# Add current working directory to path to resolve imports
sys.path.append(os.getcwd())

from backend.rag.prompt_builder import build_prompt
from backend.rag.llm_client import call_llm

print("Building prompt...")
mock_context = "### main.py\n```python\nprint('hello world')\n```"
messages = build_prompt(
    query="How does the main entry point work?",
    context=mock_context,
    history=[],
    repo_meta={"description": "Mock project", "tech_stack": ["Python"]}
)

print("Calling LLM...")
try:
    res = call_llm(messages)
    print("LLM Call Success!")
    print("Response length:", len(res))
    print("Response preview:", res[:200])
except Exception as e:
    print("LLM Call Error:", type(e).__name__, e)
