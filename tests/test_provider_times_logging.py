import importlib
import utils.deepseek_client as dsc
import pytest


@pytest.mark.asyncio
async def test_provider_times_logged_and_returned(caplog, monkeypatch):
    at = importlib.import_module("tools.answer_tool")

    docs = [{"id": "d1", "title": "T1", "text": "txt", "score": 0.9}]

    async def fake_search(q, limit=4):
        return docs, {"local_provider": 42}

    # patch aggregator
    importlib.import_module("tools.aggregator_tool")
    from tools import aggregator_tool as real_agg

    real_agg.search = fake_search

    async def fake_generate(prompt, *args, **kwargs):
        return {"answer": "ok", "sources": [{"id": "d1"}]}

    monkeypatch.setattr(dsc, "generate", fake_generate)

    caplog.set_level("INFO")
    res = await at.answer("Q", limit=1)

    assert res["debug"]["provider_times_ms"]["local_provider"] == 42
    # ensure log contains provider_times key or compact JSON
    logs = "\n".join([r.getMessage() for r in caplog.records])
    assert "provider_times" in logs or "provider_times_json" in logs
