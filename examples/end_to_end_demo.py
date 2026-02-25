"""Simple end-to-end demo script for local backend.

This script invokes `tools.answer_tool.answer_sync` with a mocked Deepseek
generate implementation to produce a deterministic natural-language answer.
It writes the result to `out/demo_result.json` for CI artifact upload or manual inspection.
"""

import json
import os
import asyncio

from utils import deepseek_client


async def _run():
    # ensure out dir
    out_dir = os.path.join(os.path.dirname(__file__), "..", "out")
    os.makedirs(out_dir, exist_ok=True)

    # simple mock of deepseek generate
    async def _mock_generate(prompt, **k):
        return {
            "answer": "演示回答：这是一个由本地 mock Deepseek 生成的回答。",
            "sources": [],
        }

    # patch generate
    deepseek_client.generate = _mock_generate

    # call answer flow
    try:
        from tools import answer_tool

        resp = await answer_tool.answer("卷积神经网络主要用于什么？", limit=3)
    except Exception as e:
        resp = {"error": str(e)}

    out_path = os.path.join(out_dir, "demo_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resp, f, ensure_ascii=False, indent=2)

    print("Wrote demo output to:", out_path)


if __name__ == "__main__":
    asyncio.run(_run())
