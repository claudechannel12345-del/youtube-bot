"""Shared LLM text-generation helper.

Default provider is OpenAI. Set LLM_PROVIDER=gemini to use the existing Gemini
path as a fallback.
"""

from __future__ import annotations

import os
import time


OPENAI_KEY_FILE = r"C:\Users\Caden\.youtube_bot_openai_key.txt"
GEMINI_KEY_FILE = r"C:\Users\Caden\.youtube_bot_gemini_key.txt"


def _inject_truststore():
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        pass


def _load_key(path: str, env: str) -> None:
    # Project key files are authoritative; overwrite stale inherited env values.
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            os.environ[env] = f.read().strip()


def _load_project_keys() -> None:
    _load_key(OPENAI_KEY_FILE, "OPENAI_API_KEY")
    _load_key(GEMINI_KEY_FILE, "GEMINI_API_KEY")


def load_project_keys() -> None:
    """Load authoritative project LLM keys into the process environment."""
    _load_project_keys()


def _openai_model(tier: str) -> str:
    if tier == "cheap":
        return os.environ.get("OPENAI_MODEL_CHEAP", "gpt-5-mini")
    return os.environ.get("OPENAI_MODEL", "gpt-5.5")


def _is_transient_openai_error(error: Exception) -> tuple[bool, float]:
    msg = str(error)
    lower = msg.lower()
    if "429" in msg or "rate" in lower:
        return True, 20.0
    transient_markers = ("500", "502", "503", "504", "timeout", "apiconnection", "temporarily")
    if any(marker in lower for marker in transient_markers):
        return True, 8.0
    return False, 0.0


def _generate_openai(prompt: str, *, tier: str, json_mode: bool) -> str:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set and no project key file was found")

    client = OpenAI(api_key=api_key)
    kwargs = {
        "model": _openai_model(tier),
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_err = None
    for attempt in range(4):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_err = exc
            retry, delay = _is_transient_openai_error(exc)
            if retry and attempt < 3:
                time.sleep(delay)
                continue
            raise
    raise last_err if last_err else RuntimeError("OpenAI generation failed")


def _gemini_models(tier: str):
    from gemini_utils import MODELS, PRO_MODELS

    return MODELS if tier == "cheap" else PRO_MODELS


def _response_text(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text
    try:
        parts = response.candidates[0].content.parts
        return "".join(str(getattr(part, "text", "") or "") for part in parts)
    except Exception:
        return str(response)


def _generate_gemini(prompt: str, *, tier: str, json_mode: bool) -> str:
    from google import genai
    from google.genai import types
    from gemini_utils import generate

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set and no project key file was found")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=75000),
    )
    response = generate(client, prompt, models=_gemini_models(tier))
    return _response_text(response)


def llm_generate(prompt, *, tier="quality", json_mode=False, provider=None) -> str:
    """Generate text from the configured LLM provider."""
    _inject_truststore()
    _load_project_keys()

    normalized_tier = str(tier or "quality").strip().lower()
    if normalized_tier not in ("quality", "cheap"):
        normalized_tier = "quality"

    selected = str(provider or os.environ.get("LLM_PROVIDER", "openai")).strip().lower()
    if selected == "openai":
        return _generate_openai(str(prompt), tier=normalized_tier, json_mode=bool(json_mode))
    if selected == "gemini":
        return _generate_gemini(str(prompt), tier=normalized_tier, json_mode=bool(json_mode))
    raise ValueError("Unsupported LLM_PROVIDER %r; expected 'openai' or 'gemini'" % selected)
