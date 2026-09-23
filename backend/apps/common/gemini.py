"""Thin, synchronous client for AI text/JSON completions.

Shared by every feature that needs one — `apps.remedial` (topic explanations
+ practice games), `apps.learning` (AI-generated tests), `apps.games` (the
self-serve practice games catalog). Gemini is the primary provider; Groq is
an automatic fallback tried whenever Gemini doesn't return a usable
completion — quota/rate-limit exhaustion, a network error, or no Gemini key
configured at all. Never raises: if both providers fail (or neither is
configured) it logs and returns `None`, the same "fail quiet" contract as
`apps.telegram_bot.services.send_telegram_message`, so a down/overloaded AI
provider degrades a feature rather than 500ing it.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_gemini(prompt: str, json_mode: bool) -> str | None:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None

    generation_config = {"temperature": 0.7}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    url = _GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL)

    try:
        # The key goes in a header, not the query string, so it never ends up
        # in request-URL logs (urllib3 debug logging, proxies, error traces).
        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            json=payload,
            timeout=30,
        )
        if response.status_code == 429:
            logger.warning("Gemini quota/rate limit hit — falling back to Groq.")
            return None
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.RequestException:
        logger.warning("Gemini request failed — falling back to Groq.")
        return None
    except (KeyError, IndexError, ValueError):
        logger.warning("Unexpected Gemini response shape — falling back to Groq.")
        return None


def _call_groq(prompt: str, json_mode: bool) -> str | None:
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return None

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException:
        logger.warning("Groq request failed.")
        return None
    except (KeyError, IndexError, ValueError):
        logger.warning("Unexpected Groq response shape.")
        return None


def call_gemini(*, prompt: str, json_mode: bool = False) -> str | None:
    text = _call_gemini(prompt, json_mode)
    if text is not None:
        return text
    return _call_groq(prompt, json_mode)
