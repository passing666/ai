import os
import logging
import asyncio
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
    return provided or os.getenv("DEEPSEEK_ENDPOINT") or "https://api.deepseek.com/v1/chat/completions"


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
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}

    attempt = 0
    last_exc = None
    while True:
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.exception("Deepseek API returned HTTP error on attempt %s", attempt)
            status = getattr(e.response, "status_code", None)
            if status and 400 <= status < 500 and status != 429:
                raise DeepseekError(f"Deepseek HTTP error: {status}") from e
            last_exc = e
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            logger.warning("Transient network error on attempt %s: %s", attempt, e)
            last_exc = e
        except Exception as e:
            logger.exception("Unexpected error when calling Deepseek on attempt %s", attempt)
            last_exc = e

        if attempt > retries:
            logger.error("Deepseek request failed after %s attempts", attempt)
            raise DeepseekError("Deepseek request failed") from last_exc

        await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))


def generate_sync(
    prompt: str, timeout: float = 15.0, endpoint: str | None = None, retries: int = 2
) -> dict:
    """Synchronous wrapper for convenience."""
    return asyncio.get_event_loop().run_until_complete(
        generate(prompt, timeout=timeout, endpoint=endpoint, retries=retries)
    )
