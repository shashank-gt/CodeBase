import os
import sys

# Add current working directory to path to resolve imports
sys.path.append(os.getcwd())

from backend.rag.prompt_builder import build_prompt
from backend.rag.llm_client import _groq_call

print("Building exact prompt...")
mock_context = "### main.py\n```python\nprint('hello world')\n```"
messages = build_prompt(
    query="How does the main entry point work?",
    context=mock_context,
    history=[],
    repo_meta={"description": "Mock project", "tech_stack": ["Python"]}
)

print("Calling Groq directly...")
try:
    res = _groq_call(messages)
    print("Groq direct success!")
    print("Response preview:", res[:200])
except Exception as e:
    print("Groq direct error:", type(e).__name__, e)
    if hasattr(e, 'response') and e.response is not None:
        print("Status code:", e.response.status_code)
        print("Response body:", e.response.text)
