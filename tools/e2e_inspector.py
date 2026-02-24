"""E2E & Inspector demo runner.

This script runs a demo of the backend answer flow and prepares Inspector-friendly
artifacts: a JSON result with `debug` fields and a Prometheus metrics text file.

Usage:
  python -m tools.e2e_inspector --question "问题" --mode stub --metrics-file ./out/metrics.txt --serve

Notes:
- Does not modify `server.py` or `modules/YA_Common`.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from typing import Dict, Any


def run(question: str, limit: int = 4, mode: str = "stub", metrics_file: str = "./metrics.txt", serve: bool = False, port: int = 8000) -> Dict[str, Any]:
    # Lazy imports to keep module lightweight
    import importlib

    local_adapter = importlib.import_module("tools.local_adapter")
    metrics_exporter = importlib.import_module("tools.metrics_exporter")

    # Run demo (calls tools.answer_tool.answer())
    out = None
    try:
        out = local_adapter.run_demo(question, limit=limit, mode=mode)
        # run_demo is async function; ensure we await if necessary
        import asyncio

        if asyncio.iscoroutine(out):
            out = asyncio.run(out)
    except Exception as e:
        return {"error": str(e)}

    # write metrics file if debug/provider_times present
    provider_times = out.get("result", {}).get("debug", {}).get("provider_times_ms", {})
    try:
        metrics_exporter.write_metrics_file(provider_times, metrics_file)
    except Exception:
        # non-fatal
        pass

    # Optionally serve metrics file in background thread
    if serve:
        def _serve():
            try:
                metrics_exporter.run_http_server(metrics_file, port=port)
            except Exception:
                return

        t = threading.Thread(target=_serve, daemon=True)
        t.start()
        # give server a moment to start
        time.sleep(0.2)

    # Also dump inspector JSON to stdout (caller can redirect)
    inspector = {"result": out.get("result"), "metrics_file": metrics_file}
    return inspector


def _cli():
    parser = argparse.ArgumentParser(description="Run E2E Inspector demo (stub or real)")
    parser.add_argument("--question", required=True)
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--mode", choices=["stub", "real"], default="stub")
    parser.add_argument("--metrics-file", default="./metrics.txt")
    parser.add_argument("--serve", action="store_true", help="Serve metrics file over HTTP")
    parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    inspector = run(args.question, limit=args.limit, mode=args.mode, metrics_file=args.metrics_file, serve=args.serve, port=args.port)
    print(json.dumps(inspector, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
