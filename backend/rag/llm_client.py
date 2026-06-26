"""
LLM client for CBQA V8 — Production Release.
Primary:  Groq (llama-3.3-70b-versatile)
Fallback: Gemini (only when GEMINI_API_KEY is set and Groq fails)
Features: Automatic retry with backoff, rate limit handling,
          token estimation, and clean error propagation.
"""
import logging
import time
import requests as _requests
from typing import List, Dict

from config.settings import settings

logger = logging.getLogger(__name__)

# ── State ─────────────────────────────────────────────────────────────────────

_gemini_genai = None  # lazy-loaded google.generativeai module
_active_provider: str = settings.LLM_PROVIDER
_MAX_RETRIES = 3  # Groq rate-limit / transient retries


def get_active_provider() -> str:
    """Return the provider that served the last request."""
    return _active_provider


# ── Token estimation ──────────────────────────────────────────────────────────

def _estimate_tokens(messages: List[Dict]) -> int:
    """Rough token estimate (~2.5 chars per token for code/text mixture)."""
    total = sum(len(m.get("content", "")) for m in messages)
    return int(total / 2.5)


def _trim_context_if_needed(messages: List[Dict], provider: str = None) -> List[Dict]:
    """Trim the retrieved code context if the entire messages payload exceeds token limits."""
    if provider == "groq":
        # Groq has a 12000 token limit per request for llama-3.3-70b-versatile
        # Request total = input tokens + max_tokens
        max_context_tokens = 11000 - settings.LLM_MAX_TOKENS
    elif provider == "gemini":
        max_context_tokens = 250000  # Gemini-2.5-flash context window is 1M
    else:
        max_context_tokens = 12000 - settings.LLM_MAX_TOKENS

    est = _estimate_tokens(messages)
    if est <= max_context_tokens:
        return messages

    logger.warning(f"Context too large (~{est} tokens) for provider '{provider}', trimming to fit {max_context_tokens} tokens")
    
    trimmed_messages = [dict(m) for m in messages]
    
    for idx, m in enumerate(trimmed_messages):
        if m["role"] == "user":
            content = m["content"]
            context_header = "\n## Retrieved Code Context\n"
            question_header = "\n\n---\n\n## Question\n"
            
            if context_header in content and question_header in content:
                parts_before = content.split(context_header)
                prefix = parts_before[0] + context_header
                
                parts_after = parts_before[1].split(question_header)
                retrieved_context = parts_after[0]
                suffix = question_header + parts_after[1]
                
                file_blocks = retrieved_context.split("\n\n---\n\n")
                
                base_messages = [dict(msg) for msg in trimmed_messages]
                base_messages[idx]["content"] = prefix + suffix
                
                base_tokens = _estimate_tokens(base_messages)
                current_tokens = base_tokens
                
                keep_blocks = []
                for block in file_blocks:
                    block_tokens = len(block) // 4
                    if current_tokens + block_tokens + 5 <= max_context_tokens:
                        keep_blocks.append(block)
                        current_tokens += block_tokens + 5
                    else:
                        if not keep_blocks:
                            trimmed_block = block[:max(100, (max_context_tokens - current_tokens) * 4 - 100)]
                            if len(trimmed_block) > 100:
                                keep_blocks.append(trimmed_block + "\n\n[... first file block truncated for token limit ...]")
                        break
                
                new_context = "\n\n---\n\n".join(keep_blocks) if keep_blocks else "No code context could fit within the token limit."
                trimmed_messages[idx]["content"] = prefix + new_context + suffix
                new_est = _estimate_tokens(trimmed_messages)
                logger.info(f"Trimmed context size from {est} to {new_est} tokens")
                return trimmed_messages
            else:
                safe_chars = max_context_tokens * 4
                if len(content) > safe_chars:
                    trimmed_messages[idx]["content"] = content[:safe_chars] + "\n\n[... content truncated for token limit ...]"
                    return trimmed_messages
                    
    return trimmed_messages


# ── Lazy Gemini init ──────────────────────────────────────────────────────────

def _init_gemini():
    global _gemini_genai
    if _gemini_genai is not None:
        return _gemini_genai
    key = settings.GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY is not set in .env")
    from google import genai
    _gemini_genai = genai.Client(api_key=key)
    return _gemini_genai


# ── Public entry point ────────────────────────────────────────────────────────

def call_llm(messages: List[Dict]) -> str:
    """
    Route an LLM request with automatic failover.
    - groq:  Try Groq first. Fall back to Gemini if configured.
    - gemini: Use Gemini directly.
    - local:  Use Ollama.
    """
    global _active_provider
    provider = settings.LLM_PROVIDER

    # Trim context if too large based on provider
    messages = _trim_context_if_needed(messages, provider=provider)

    if provider == "groq":
        try:
            result = _groq_call(messages)
            _active_provider = "groq"
            return result
        except Exception as groq_err:
            logger.warning(f"Groq failed ({type(groq_err).__name__}): {groq_err}")

            # Attempt Gemini fallback
            gemini_key = settings.GEMINI_API_KEY
            if not gemini_key:
                raise RuntimeError(
                    f"Groq failed and no GEMINI_API_KEY configured for fallback. "
                    f"Error: {groq_err}"
                ) from groq_err

            logger.info("Falling back to Gemini...")
            try:
                result = _gemini_call(messages)
                _active_provider = "gemini (fallback)"
                return result
            except Exception as gem_err:
                logger.error(f"Gemini fallback also failed: {gem_err}")
                if "API key not valid" in str(gem_err) or "INVALID_ARGUMENT" in str(gem_err):
                    raise RuntimeError(
                        f"Groq failed, and Gemini fallback failed because the configured GEMINI_API_KEY is invalid."
                    ) from gem_err
                raise RuntimeError(
                    f"All LLM providers failed. Groq: {type(groq_err).__name__}. "
                    f"Gemini: {type(gem_err).__name__}."
                ) from gem_err

    elif provider == "gemini":
        try:
            result = _gemini_call(messages)
            _active_provider = "gemini"
            return result
        except Exception as gem_err:
            if "API key not valid" in str(gem_err) or "INVALID_ARGUMENT" in str(gem_err):
                raise ValueError("Gemini API call failed: The configured GEMINI_API_KEY is invalid. Please check your .env file.") from gem_err
            raise
    else:
        result = _ollama_call(messages)
        _active_provider = "local"
        return result


# ── Groq (primary) ────────────────────────────────────────────────────────────

def _groq_call(messages: List[Dict]) -> str:
    """Call Groq with automatic retry and exponential backoff on rate limits."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in .env")

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "stream": False,
    }

    last_err: Exception = RuntimeError("Groq: unknown failure")

    for attempt in range(_MAX_RETRIES):
        try:
            resp = _requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=settings.GROQ_TIMEOUT,
            )

            if resp.status_code == 429:
                # Rate limited — use Retry-After header or exponential backoff
                wait = int(resp.headers.get("Retry-After", min(3 * (2 ** attempt), 30)))
                logger.warning(f"Groq rate-limited. Waiting {wait}s (attempt {attempt + 1}/{_MAX_RETRIES})")
                time.sleep(wait)
                last_err = RuntimeError("Groq rate-limited (429)")
                continue

            if resp.status_code >= 500:
                wait = 2 * (attempt + 1)
                last_err = RuntimeError(f"Groq server error {resp.status_code}")
                logger.warning(f"{last_err}. Retrying in {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code == 413 or resp.status_code == 400:
                # Payload too large or bad request — don't retry
                error_body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_body.get("error", {}).get("message", resp.text[:200])
                raise ValueError(f"Groq rejected request ({resp.status_code}): {error_msg}")

            resp.raise_for_status()

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if not content:
                raise ValueError("Groq returned empty response")
            return content

        except _requests.exceptions.Timeout:
            last_err = TimeoutError(
                f"Groq timed out after {settings.GROQ_TIMEOUT}s (attempt {attempt + 1}/{_MAX_RETRIES})"
            )
            logger.warning(str(last_err))
            if attempt < _MAX_RETRIES - 1:
                time.sleep(2)

        except _requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot reach Groq API: {e}") from e

        except (ValueError, KeyError) as e:
            # Don't retry on bad responses
            raise

        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep(2)

    raise last_err


# ── Gemini (fallback) ────────────────────────────────────────────────────────

def _gemini_call(messages: List[Dict]) -> str:
    """Call Gemini with proper message formatting using google-genai SDK."""
    client = _init_gemini()
    from google.genai import types

    sys_parts = []
    contents = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "system":
            sys_parts.append(content)
        elif role in ("user", "assistant"):
            contents.append(
                types.Content(
                    role="user" if role == "user" else "model",
                    parts=[types.Part.from_text(text=content)]
                )
            )

    if not contents:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Hello")]
            )
        )

    system_instruction = "\n\n".join(sys_parts) if sys_parts else None

    config = types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE,
        max_output_tokens=settings.LLM_MAX_TOKENS,
        system_instruction=system_instruction,
    )

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        text = response.text
        if not text:
            raise ValueError("Gemini returned empty response")
        return text
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise


# ── Ollama / local (optional) ─────────────────────────────────────────────────

def _ollama_call(messages: List[Dict]) -> str:
    """Call local Ollama instance."""
    url = f"{settings.LOCAL_LLM_URL}/v1/chat/completions"
    try:
        r = _requests.post(
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
        content = r.json()["choices"][0]["message"]["content"]
        if not content:
            raise ValueError("Ollama returned empty response")
        return content
    except _requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            f"Cannot reach Ollama at {settings.LOCAL_LLM_URL}. Is it running?"
        ) from e
