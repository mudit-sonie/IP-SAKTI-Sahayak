"""Answer translation (roadmap S15, scaffold).

Translates a *generated answer* into an Indian language as a post-processing
step. Citations, quoted statute text, and section references stay verbatim
English — only the assistant's prose is translated, and inline `[n]` markers are
preserved so the footnote links still work.

If Gemini is unavailable the caller keeps the English answer; nothing is faked.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.llm.gemini_client import GeminiUnavailable, get_gemini_client

logger = get_logger(__name__)

SUPPORTED: dict[str, str] = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
}


def languages() -> list[dict[str, str]]:
    return [{"code": "en", "name": "English"}] + [
        {"code": code, "name": name} for code, name in SUPPORTED.items()
    ]


def translate(text: str, lang: str) -> str | None:
    text = (text or "").strip()
    if not text or lang == "en" or lang not in SUPPORTED:
        return None
    client = get_gemini_client()
    if not client.is_configured:
        logger.info("translation requested but Gemini unavailable")
        return None
    prompt = (
        f"Translate the assistant answer below into {SUPPORTED[lang]}.\n"
        "Rules:\n"
        "- Keep every bracketed marker like [1] or [2][3] exactly as written and "
        "in the same position.\n"
        "- Do NOT translate the names of statutes, Acts, Rules, treaties, section "
        "or article numbers, or institutions — leave those in English.\n"
        "- Preserve paragraph breaks.\n"
        'Return JSON: {"translation": string}.\n\n'
        f"ANSWER:\n{text}"
    )
    try:
        data = client.generate_json(prompt, temperature=0.1)
    except GeminiUnavailable as exc:
        logger.warning("translation failed: %s", exc)
        return None
    out = str(data.get("translation") or "").strip()
    return out or None
