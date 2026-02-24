import pytest
import asyncio

from tools import answer_tool


class DummyDeepseekError(Exception):
    pass


@pytest.mark.asyncio
async def test_answer_degraded_when_deepseek_fails(monkeypatch):
    async def fake_search(q, limit):
        return ([{"id":"1","title":"t","text":"txt","score":0.9}], {"local_provider": 10})

    async def fake_generate(prompt, *args, **kwargs):
        raise Exception("network")

    monkeypatch.setattr("tools.aggregator_tool.search", fake_search)
    monkeypatch.setattr("utils.deepseek_client.generate", fake_generate)

    resp = await answer_tool.answer("测试问题", limit=2)
    assert "answer" in resp
    assert "debug" in resp
    assert resp["debug"].get("deepseek_error") is not None


@pytest.mark.asyncio
async def test_answer_success_mapping(monkeypatch):
    async def fake_search(q, limit):
        return ([{"id":"1","title":"t","text":"txt","score":0.9}], {"local_provider": 12})

    async def fake_generate(prompt, *args, **kwargs):
        return {"answer": "这是生成的答案", "sources": [{"id":"1", "url":"http://example.com"}]}

    monkeypatch.setattr("tools.aggregator_tool.search", fake_search)
    monkeypatch.setattr("utils.deepseek_client.generate", fake_generate)

    resp = await answer_tool.answer("另一个问题", limit=2)
    assert resp["answer"] == "这是生成的答案"
    assert isinstance(resp["citations"], list)
    assert resp["debug"]["provider_times_ms"]["local_provider"] == 12
