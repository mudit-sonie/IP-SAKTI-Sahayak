"""Gemini client with multi-key rotation.

Ports the HackRx ``brain.py`` pattern: hold N API keys, round-robin through them,
and on a quota / rate-limit / transient error advance to the next key and retry.
Free-tier Gemini keys have low RPM/RPD limits, so rotation is what keeps the demo
alive during a live Q&A.

The rest of the app should depend only on ``GeminiClient.generate_json`` — never
import ``google.generativeai`` directly.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Substrings that mean "this key is exhausted / throttled, try the next one".
_ROTATE_ON = (
    "429",
    "quota",
    "rate limit",
    "resource has been exhausted",
    "resourceexhausted",
    "503",
    "unavailable",
    "500",
    "internal error",
)


class GeminiUnavailable(RuntimeError):
    """Raised when every key has been tried and none produced a response."""


class GeminiClient:
    def __init__(
        self,
        api_keys: Optional[list[str]] = None,
        model: Optional[str] = None,
        max_attempts_per_key: int = 2,
    ) -> None:
        settings = get_settings()
        self._keys = list(api_keys if api_keys is not None else settings.gemini_key_list)
        self._model_name = model or settings.gemini_model
        self._max_attempts_per_key = max_attempts_per_key
        self._cursor = 0
        self._sdk = self._try_import_sdk()

    @staticmethod
    def _try_import_sdk() -> Any | None:
        try:
            import google.generativeai as genai  # type: ignore

            return genai
        except Exception:  # pragma: no cover - env without the dep
            logger.warning("google-generativeai not installed; GeminiClient disabled")
            return None

    @property
    def is_configured(self) -> bool:
        return bool(self._keys) and self._sdk is not None

    def _ordered_keys(self) -> list[tuple[int, str]]:
        """Keys starting from the current cursor, so we resume where we left off."""
        n = len(self._keys)
        return [((self._cursor + i) % n, self._keys[(self._cursor + i) % n]) for i in range(n)]

    def generate_json(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Call Gemini and parse its response as JSON.

        Raises ``GeminiUnavailable`` if all keys fail. Callers are expected to
        catch that and fall back to an ``escalate`` response.
        """
        if not self.is_configured:
            raise GeminiUnavailable("no Gemini keys configured or SDK missing")

        last_err: Optional[Exception] = None
        for key_index, key in self._ordered_keys():
            for attempt in range(self._max_attempts_per_key):
                try:
                    raw = self._invoke(key, prompt, system_instruction, temperature)
                    self._cursor = key_index  # stick with the key that worked
                    return self._parse_json(raw)
                except Exception as exc:  # noqa: BLE001 - classify by message
                    last_err = exc
                    msg = str(exc).lower()
                    if any(tok in msg for tok in _ROTATE_ON):
                        logger.warning(
                            "gemini key #%d throttled/errored, rotating: %s",
                            key_index,
                            exc,
                        )
                        break  # next key
                    if attempt + 1 < self._max_attempts_per_key:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    logger.warning("gemini key #%d failed: %s", key_index, exc)
                    break
        raise GeminiUnavailable(f"all {len(self._keys)} Gemini keys failed: {last_err}")

    def _invoke(
        self,
        key: str,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
    ) -> str:
        genai = self._sdk
        assert genai is not None
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            self._model_name,
            system_instruction=system_instruction,
            generation_config={
                "temperature": temperature,
                "response_mime_type": "application/json",
            },
        )
        resp = model.generate_content(prompt)
        return (resp.text or "").strip()

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        if not raw:
            raise ValueError("empty response from Gemini")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Models sometimes wrap JSON in ```json fences despite the mime type.
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
            start, end = cleaned.find("{"), cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start : end + 1])
            raise


_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
