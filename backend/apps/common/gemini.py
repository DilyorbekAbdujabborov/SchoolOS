"""Thin, synchronous client for Google Gemini's `generateContent` API.

Shared by every feature that needs an AI text/JSON completion —
`apps.remedial` (topic explanations + practice games), `apps.learning`
(AI-generated tests), `apps.games` (the self-serve practice games catalog).
Never raises: on any failure it logs and returns `None`, the same "fail
quiet" contract as `apps.telegram_bot.services.send_telegram_message`, so a
down/overloaded AI provider degrades a feature rather than 500ing it.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def call_gemini(*, prompt: str, json_mode: bool = False) -> str | None:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set — cannot call Gemini.")
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
        response = requests.post(
            url,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.RequestException:
        logger.warning("Gemini request failed.")
        return None
    except (KeyError, IndexError, ValueError):
        logger.warning("Unexpected Gemini response shape.")
        return None
