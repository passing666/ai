import os
import logging
import asyncio
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class DeepseekError(Exception):
    pass


def _get_api_key() -> str:
    """Read DEEPSEEK_API_KEY from environment at call time and raise a friendly error if missing."""
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise DeepseekError(
            "DEEPSEEK_API_KEY not found. Set it in environment or in a .env file."
        )
    return key


def _get_endpoint(provided: str | None) -> str:
    return (
        provided
        or os.getenv("DEEPSEEK_ENDPOINT")
        or "https://api.deepseek.com/v1/chat/completions"
    )


# Circuit breaker (simple in-memory implementation)
_CIRCUIT_FAIL_COUNT = 0
_CIRCUIT_LAST_FAILURE_TS: Optional[float] = None


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _circuit_is_open() -> bool:
    global _CIRCUIT_FAIL_COUNT, _CIRCUIT_LAST_FAILURE_TS
    threshold = _env_int("DEEPSEEK_CIRCUIT_THRESHOLD", 5)
    cooldown = _env_int("DEEPSEEK_CIRCUIT_COOLDOWN", 60)
    if _CIRCUIT_FAIL_COUNT >= threshold and _CIRCUIT_LAST_FAILURE_TS:
        if time.time() - _CIRCUIT_LAST_FAILURE_TS < cooldown:
            return True
        # cooldown passed -> reset
        _CIRCUIT_FAIL_COUNT = 0
        _CIRCUIT_LAST_FAILURE_TS = None
    return False


def _record_failure():
    global _CIRCUIT_FAIL_COUNT, _CIRCUIT_LAST_FAILURE_TS
    _CIRCUIT_FAIL_COUNT += 1
    _CIRCUIT_LAST_FAILURE_TS = time.time()


def _reset_circuit():
    global _CIRCUIT_FAIL_COUNT, _CIRCUIT_LAST_FAILURE_TS
    _CIRCUIT_FAIL_COUNT = 0
    _CIRCUIT_LAST_FAILURE_TS = None


async def generate(
    prompt: str,
    timeout: float = 15.0,
    endpoint: str | None = None,
    retries: int = 2,
    backoff_factor: float = 0.5,
) -> dict:
    """Call Deepseek generate endpoint with retries and timeout.

    Reads `DEEPSEEK_API_KEY` at call time so tests can monkeypatch env.
    Raises `DeepseekError` on missing key or request failure.
    """
    api_key = _get_api_key()
    url = _get_endpoint(endpoint)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Deepseek chat endpoint expects model + messages payload (chat format)
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
    }

    attempt = 0
    last_exc = None
    while True:
        # check circuit breaker before attempt
        if _circuit_is_open():
            raise DeepseekError(
                "Deepseek circuit open (recent failures); request blocked"
            )
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # Normalize chat/completion style responses into {'answer': str, 'sources': []}
                if isinstance(data, dict):
                    # If Deepseek returned chat.completion structure, extract assistant message
                    choices = data.get("choices")
                    if choices and isinstance(choices, list):
                        first = choices[0]
                        # support both {"message": {"content": ...}} and legacy {"text": ...}
                        msg = first.get("message") if isinstance(first, dict) else None
                        content = None
                        if isinstance(msg, dict):
                            content = msg.get("content")
                        if not content:
                            content = (
                                first.get("text") if isinstance(first, dict) else None
                            )
                        if content:
                            _reset_circuit()
                            return {
                                "answer": content,
                                **{k: v for k, v in data.items() if k != "choices"},
                            }
                    # If API already returns {'answer': ...}, pass through
                    if "answer" in data:
                        _reset_circuit()
                        return data
                _reset_circuit()
                return data
        except httpx.HTTPStatusError as e:
            logger.exception("Deepseek API returned HTTP error on attempt %s", attempt)
            status = getattr(e.response, "status_code", None)
            # treat client errors (except 429) as fatal
            if status and 400 <= status < 500 and status != 429:
                _record_failure()
                raise DeepseekError(f"Deepseek HTTP error: {status}") from e
            # 429 should be retried (backoff below)
            last_exc = e
            _record_failure()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            logger.warning("Transient network error on attempt %s: %s", attempt, e)
            last_exc = e
            _record_failure()
        except Exception as e:
            logger.exception(
                "Unexpected error when calling Deepseek on attempt %s", attempt
            )
            last_exc = e
            _record_failure()

        if attempt > retries:
            logger.error("Deepseek request failed after %s attempts", attempt)
            raise DeepseekError("Deepseek request failed") from last_exc

        # exponential backoff before retrying; increase backoff on 429
        sleep_sec = backoff_factor * (2 ** (attempt - 1))
        try:
            # if last_exc looks like an HTTPStatusError with 429, increase backoff
            if isinstance(last_exc, httpx.HTTPStatusError):
                status = getattr(last_exc.response, "status_code", None)
                if status == 429:
                    sleep_sec = max(sleep_sec, 5.0)
        except Exception:
            pass

        # if we are about to retry and next attempt will happen, allow brief sleep
        await asyncio.sleep(sleep_sec)
    # end while


def generate_sync(
    prompt: str, timeout: float = 15.0, endpoint: str | None = None, retries: int = 2
) -> dict:
    """Synchronous wrapper for convenience."""
    return asyncio.get_event_loop().run_until_complete(
        generate(prompt, timeout=timeout, endpoint=endpoint, retries=retries)
    )
