import importlib
import pytest


@pytest.mark.asyncio
async def test_reranker_integration(monkeypatch):
    at = importlib.import_module("tools.answer_tool")

    docs = [
        {"id": "d1", "title": "A", "text": "苹果 香蕉 苹果", "score": 0.1},
        {"id": "d2", "title": "B", "text": "香蕉 苹果 橘子", "score": 0.2},
        {"id": "d3", "title": "C", "text": "橘子 西瓜", "score": 0.05},
    ]

    async def fake_search(q, limit=4):
        return docs, {"local": 10}

    async def fake_generate(prompt, *args, **kwargs):
        return {"answer": "ok", "sources": [{"id": "d2"}]}

    # patch aggregator
    at.aggregator_tool = type("X", (), {"search": staticmethod(fake_search)})

    import utils.deepseek_client as dsc

    monkeypatch.setattr(dsc, "generate", fake_generate)

    # Call with reranker enabled - expect top doc to be one with more overlap
    res = await at.answer("苹果", limit=2, use_reranker=True)
    assert "answer" in res
    # sources should include id from fake_generate
    assert res["citations"][0]["id"] == "d2"
