import pytest

import httpx

from utils import deepseek_client


@pytest.mark.asyncio
async def test_circuit_breaker_trips(monkeypatch):
    # ensure key present
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy")

    class BadClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *a, **kw):
            raise httpx.ConnectError("simulated")

    monkeypatch.setattr(httpx, "AsyncClient", BadClient)

    # reset internal circuit state if present
    try:
        deepseek_client._reset_circuit()
    except Exception:
        pass

    # call repeatedly until circuit opens
    opened = False
    # default threshold is 5, try a few more iterations
    for i in range(10):
        with pytest.raises(deepseek_client.DeepseekError) as ctx:
            await deepseek_client.generate("prompt", retries=0)
        if "circuit open" in str(ctx.value):
            opened = True
            break

    assert opened, "circuit did not open after repeated failures"
