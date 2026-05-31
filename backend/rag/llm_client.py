"""
LLM client: supports Gemini, Groq, and local Ollama.
Provides robust safety fallbacks and high-performance execution.
Uses the modern Google GenAI SDK for Gemini.
Includes automatic bidirectional fallback (Groq <-> Gemini) as a backup system.
"""
import logging
from typing import List, Dict
from config.settings import settings

logger = logging.getLogger(__name__)

# ── Lazy-loaded clients ───────────────────────────────────────────────────────

_gemini_client = None
_groq_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env")
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


def _get_groq():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env")
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


# ── Main entry point with backup fallback ─────────────────────────────────────

def call_llm(messages: List[Dict]) -> str:
    """
    Call the configured LLM (Gemini, Groq, or local Ollama).
    Provides automatic fallback to the backup provider (Gemini <-> Groq)
    if the primary provider encounters an exception and both keys are set.
    """
    provider = settings.LLM_PROVIDER

    try:
        if provider == "gemini":
            return _gemini_call(messages)
        elif provider == "groq":
            return _groq_call(messages)
        else:
            return _ollama_call(messages)
    except Exception as e:
        logger.warning(f"Primary LLM provider ({provider}) failed: {e}")
        
        # ── Automatic Backup Fallback Mechanism ──
        if provider == "groq" and settings.GEMINI_API_KEY:
            logger.info("Attempting automatic fallback to Gemini backup provider...")
            try:
                # Add a notice about the fallback to log output
                res = _gemini_call(messages)
                logger.info("Successfully recovered using Gemini backup provider!")
                return res
            except Exception as gemini_err:
                logger.error(f"Fallback to Gemini also failed: {gemini_err}")
                raise e
        elif provider == "gemini" and settings.GROQ_API_KEY:
            logger.info("Attempting automatic fallback to Groq backup provider...")
            try:
                # Add a notice about the fallback to log output
                res = _groq_call(messages)
                logger.info("Successfully recovered using Groq backup provider!")
                return res
            except Exception as groq_err:
                logger.error(f"Fallback to Groq also failed: {groq_err}")
                raise e
        
        # Re-raise the original error if no fallback was possible or configured
        logger.error(f"LLM call failed ({provider}) and no backup fallback was available.")
        raise


# ── Gemini (Modern SDK) ───────────────────────────────────────────────────────

def _gemini_call(messages: List[Dict]) -> str:
    client = _get_gemini_client()
    from google.genai import types

    contents = []
    system_instruction = None

    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")

        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=content)]
            ))
        elif role == "assistant":
            contents.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text=content)]
            ))

    # Ensure we have at least one content
    if not contents:
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text="Hello")]
        ))

    config = types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE,
        max_output_tokens=settings.LLM_MAX_TOKENS,
        system_instruction=system_instruction
    )

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config
        )
        if response.text:
            return response.text
        
        # Check safety/block feedback if text is empty
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "finish_reason") and candidate.finish_reason:
                if str(candidate.finish_reason) not in ("FinishReason.STOP", "STOP"):
                    raise ValueError(f"Gemini call ended with finish reason: {candidate.finish_reason}")
            if hasattr(candidate, "content") and candidate.content.parts:
                return candidate.content.parts[0].text
        raise ValueError("Gemini returned an empty response. Verify API key and safety limits.")
    except Exception as e:
        logger.error(f"Gemini API failure: {e}")
        raise


# ── Groq ──────────────────────────────────────────────────────────────────────

def _groq_call(messages: List[Dict]) -> str:
    client = _get_groq()

    # Format messages to comply with OpenAI/Groq standard roles (system, user, assistant)
    formatted_messages = []
    for m in messages:
        role = m["role"]
        if role not in ("system", "user", "assistant"):
            role = "user"
        formatted_messages.append({
            "role": role,
            "content": m["content"]
        })

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=formatted_messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        if completion.choices and len(completion.choices) > 0:
            content = completion.choices[0].message.content
            if content:
                return content
        raise ValueError("Groq returned an empty response.")
    except Exception as e:
        logger.error(f"Groq API failure: {e}")
        raise


# ── Ollama (local) ────────────────────────────────────────────────────────────

def _ollama_call(messages: List[Dict]) -> str:
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
