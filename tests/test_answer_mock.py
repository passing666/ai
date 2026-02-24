import pytest

from tools import answer_tool


@pytest.mark.asyncio
async def test_answer_with_mocked_dependencies(monkeypatch):
    # mock aggregator_tool.search
    async def fake_search(q, limit=4):
        docs = [
            {"id": "d1", "title": "T1", "text": "内容一", "score": 0.9},
            {"id": "d2", "title": "T2", "text": "内容二", "score": 0.8},
        ]
        provider_times = {"local": 12}
        return docs, provider_times

    import importlib
    at = importlib.import_module("tools.answer_tool")
    # attach a fake aggregator_tool object with a search coroutine
    from types import SimpleNamespace
    at.aggregator_tool = SimpleNamespace(search=fake_search)

    # mock deepseek_client.generate
    async def fake_generate(prompt, *args, **kwargs):
        return {"answer": "这是生成的回答", "sources": [{"id": "d1"}, {"id": "d2"}]}

    import utils.deepseek_client as dsc
    monkeypatch.setattr(dsc, "generate", fake_generate)

    res = await at.answer("测试问题", limit=2)
    assert "answer" in res
    assert res["answer"] == "这是生成的回答"
    assert "debug" in res and "provider_times_ms" in res["debug"]
