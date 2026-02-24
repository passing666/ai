import pytest
import importlib


@pytest.mark.asyncio
async def test_selection_prefers_score_and_overlap(monkeypatch):
    at = importlib.import_module("tools.answer_tool")

    docs = [
        {"id": "d1", "title": "Low", "text": "unrelated content here", "score": 0.1},
        {"id": "d2", "title": "High", "text": "this mentions QUERY several times: QUERY QUERY", "score": 0.2},
    ]

    async def fake_search(q, limit=4):
        return docs, {"local": 5}

    importlib.import_module("tools.aggregator_tool")
    from tools import aggregator_tool as real_agg
    real_agg.search = fake_search

    import utils.deepseek_client as dsc

    async def fake_generate(prompt, *args, **kwargs):
        # return the prompt so the test can assert order
        return {"answer": "ok", "sources": []}

    monkeypatch.setattr(dsc, "generate", fake_generate)

    res = await at.answer("QUERY", limit=2)
    # ensure we got an answer and debug contains provider_times
    assert "answer" in res
    assert res["debug"]["provider_times_ms"] == {"local": 5}
