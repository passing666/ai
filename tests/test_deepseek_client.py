import os
import pytest
import types

from utils import deepseek_client


@pytest.mark.asyncio
async def test_generate_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(deepseek_client.DeepseekError):
        await deepseek_client.generate("hello")


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("http error")

    def json(self):
        return self._data


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json, headers):
        # return a dummy successful response
        return DummyResponse({"result": "ok"}, status_code=200)


@pytest.mark.asyncio
async def test_generate_success(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy_key")

    # monkeypatch httpx.AsyncClient used in deepseek_client
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    resp = await deepseek_client.generate("prompt here")
    assert isinstance(resp, dict)
    assert resp.get("result") == "ok"
