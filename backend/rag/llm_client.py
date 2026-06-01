"""
LLM client: supports Gemini (primary) and local Ollama.
Removed OpenAI as per user request to prevent unwanted fallback quota errors.
"""
import logging
from typing import List, Dict
from config.settings import settings

logger = logging.getLogger(__name__)

# ── Lazy-loaded clients ───────────────────────────────────────────────────────

_gemini_model = None


def _get_gemini():
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_model = genai
    return _gemini_model


# ── Main entry point ──────────────────────────────────────────────────────────

def call_llm(messages: List[Dict]) -> str:
    """Call the configured LLM (Gemini or Ollama)."""
    provider = settings.LLM_PROVIDER

    try:
        if provider == "gemini":
            return _gemini_call(messages)
        else:
            return _ollama_call(messages)
    except Exception as e:
        logger.error(f"LLM call failed ({provider}): {e}")
        raise


# ── Gemini ────────────────────────────────────────────────────────────────────

def _gemini_call(messages):
    genai = _get_gemini()

    # Extract system instruction and user/assistant messages
    system_parts = []
    chat_messages = []

    for m in messages:
        if m["role"] == "system":
            system_parts.append(m["content"])
        elif m["role"] == "user":
            chat_messages.append({"role": "user", "parts": [m["content"]]})
        elif m["role"] == "assistant":
            chat_messages.append({"role": "model", "parts": [m["content"]]})

    # Create model with system instruction if available
    system_instruction = "\n\n".join(system_parts) if system_parts else None

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_instruction,
        generation_config={
            "temperature": settings.LLM_TEMPERATURE,
            "max_output_tokens": settings.LLM_MAX_TOKENS,
        },
    )

    # Ensure we have at least one user message
    if not chat_messages:
        chat_messages = [{"role": "user", "parts": ["Hello"]}]

    response = model.generate_content(chat_messages)
    return response.text


# ── Ollama (local) ────────────────────────────────────────────────────────────

def _ollama_call(messages):
    import requests
    url = f"{settings.LOCAL_LLM_URL}/v1/chat/completions"
    try:
        r = requests.post(
            url,
            json={
                "model": settings.LOCAL_LLM_MODEL,
                "messages": messages,
                "temperature": settings.LLM_TEMPERATURE,
                "stream": False,
            },
            timeout=settings.LLM_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        if "ConnectionError" in type(e).__name__:
            raise ConnectionError(
                f"Cannot reach Ollama at {settings.LOCAL_LLM_URL}. Ensure it is running."
            )
        raise
