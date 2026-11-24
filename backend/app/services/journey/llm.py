"""Shared call to the configured chat model. Returns None when it cannot answer."""
import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def complete(system: str, user: str, timeout_s: float = 20) -> str | None:
    if not settings.LLM_API_KEY or not settings.LLM_BASE_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as http:
            response = await http.post(
                f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("Journey LLM call failed (%s); using the local fallback", type(exc).__name__)
        return None


def _parse_json(raw: str) -> dict | list | None:
    clean = raw.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:]).rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, (dict, list)) else None


async def complete_json(system: str, user: str, timeout_s: float = 12) -> dict | list | None:
    """Ask for a JSON object. Returns None when the model is absent or the body is not JSON."""
    raw = await complete(system + " Reply with JSON only.", user, timeout_s=timeout_s)
    if not raw:
        return None
    return _parse_json(raw)
