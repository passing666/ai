"""Local adapter for demonstrating backend `answer` flow without touching server.py.

Features:
- CLI to run in `stub` (fake aggregator) or `real` mode.
- Calls `tools.answer_tool.answer()` and prints JSON result + metrics lines.
- Does not modify `server.py` or `modules/YA_Common`.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
from types import SimpleNamespace
from typing import Any


async def run_demo(question: str, limit: int = 4, mode: str = "stub") -> Any:
    at = importlib.import_module("tools.answer_tool")

    if mode == "stub":

        async def fake_search(q, limit=4):
            docs = [
                {
                    "id": "stub:1",
                    "title": "示例文档一",
                    "text": "这是一段与问题相关的示例文本。",
                    "score": 0.9,
                },
                {
                    "id": "stub:2",
                    "title": "示例文档二",
                    "text": "另一段示例文本，相关性较低。",
                    "score": 0.3,
                },
            ]
            provider_times = {"local_stub": 12.0}
            return docs, provider_times

        at.aggregator_tool = SimpleNamespace(search=fake_search)

    # call the existing answer flow
    resp = await at.answer(question, limit=limit)

    # format provider metrics lines if present
    try:
        from tools.metrics import provider_times_to_metrics_lines

        provider_times = resp.get("debug", {}).get("provider_times_ms", {})
        metrics_lines = provider_times_to_metrics_lines(provider_times)
    except Exception:
        metrics_lines = ""

    out = {"result": resp, "metrics_lines": metrics_lines}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local adapter to demo backend answer flow"
    )
    parser.add_argument("question", help="Question to ask the backend")
    parser.add_argument(
        "--limit", type=int, default=4, help="Number of docs to include"
    )
    parser.add_argument(
        "--mode",
        choices=["stub", "real"],
        default="stub",
        help="Use stub aggregator or real aggregator",
    )

    args = parser.parse_args()

    out = asyncio.run(run_demo(args.question, limit=args.limit, mode=args.mode))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
