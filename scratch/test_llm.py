import os
import sys

# Add current working directory to path to resolve imports
sys.path.append(os.getcwd())

from config.settings import settings
from backend.rag.llm_client import _groq_call, _gemini_call

print("Testing Groq...")
try:
    res = _groq_call([{"role": "user", "content": "Hello"}])
    print("Groq success:", res)
except Exception as e:
    print("Groq error type:", type(e).__name__)
    print("Groq error message:", e)

print("\nTesting Gemini...")
try:
    res = _gemini_call([{"role": "user", "content": "Hello"}])
    print("Gemini success:", res)
except Exception as e:
    print("Gemini error type:", type(e).__name__)
    print("Gemini error message:", e)
