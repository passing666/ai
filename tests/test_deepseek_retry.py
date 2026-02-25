import pytest
import httpx

from utils import deepseek_client


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {"answer": "ok"}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("http error", request=None, response=self)

    def json(self):
        return self._json


class MockAsyncClient:
    # use class-level counter so separate client instances share call count
    _global_calls = 0

    def __init__(self, timeout=None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json, headers):
        MockAsyncClient._global_calls += 1
        # first call: transient connect error
        if MockAsyncClient._global_calls == 1:
            raise httpx.ConnectError("simulated")
        # second call: success
        return MockResponse(json_data={"answer": "success"})


@pytest.mark.asyncio
async def test_generate_retries_success(monkeypatch):
    # ensure circuit state is clean for this test
    try:
        deepseek_client._reset_circuit()
    except Exception:
        pass
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    res = await deepseek_client.generate("prompt", retries=2)
    assert res.get("answer") == "success"


@pytest.mark.asyncio
async def test_generate_4xx_no_retry(monkeypatch):
    # ensure circuit state is clean for this test
    try:
        deepseek_client._reset_circuit()
    except Exception:
        pass

    class Client400(MockAsyncClient):
        async def post(self, url, json, headers):
            return MockResponse(status_code=400, json_data={"error": "bad"})

    monkeypatch.setattr(httpx, "AsyncClient", Client400)
    with pytest.raises(deepseek_client.DeepseekError):
        await deepseek_client.generate("prompt", retries=1)
