import pytest
import importlib


@pytest.mark.asyncio
async def test_rag_prompt_contains_docs_and_question(monkeypatch):
    at = importlib.import_module("tools.answer_tool")

    # prepare fake docs
    docs = [
        {"id": "d1", "title": "Title One", "text": "这是第一篇文档内容。"},
        {"id": "d2", "title": "Title Two", "text": "第二篇文档的内容在这里。"},
    ]

    # monkeypatch aggregator to return our docs
    async def fake_search(q, limit=4):
        return docs, {"local": 10}

    # use monkeypatch to replace tools.aggregator_tool.search
    importlib.import_module("tools.aggregator_tool")
    from tools import aggregator_tool as real_agg

    # set attribute directly on real aggregator module
    real_agg.search = fake_search

    # capture prompt by mocking deepseek_client.generate
    import utils.deepseek_client as dsc

    captured = {}

    async def fake_generate(prompt, *args, **kwargs):
        captured["prompt"] = prompt
        return {"answer": "ok", "sources": []}

    monkeypatch.setattr(dsc, "generate", fake_generate)

    res = await at.answer("示例问题", limit=2)
    assert "answer" in res
    prompt_text = captured.get("prompt", "")
    assert "示例问题" in prompt_text
    assert "Title One" in prompt_text or "d1" in prompt_text
    assert "Title Two" in prompt_text or "d2" in prompt_text
