"""Lightweight ASGI app exposing `/answer` without modifying `server.py`.

This module lazily creates a Starlette app if `starlette` is installed. If not
installed, `create_app()` returns None so importing this module is safe in
environments without server dependencies.
"""
from __future__ import annotations

from typing import Optional


def create_app(use_reranker_default: bool = False) -> Optional[object]:
    try:
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.requests import Request
        from starlette.routing import Route
    except Exception:
        return None

    import json
    import asyncio

    async def handle_answer(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid json"}, status_code=400)

        question = body.get("question") or body.get("q")
        limit = int(body.get("limit") or 4)
        debug = bool(body.get("debug"))
        use_reranker = bool(body.get("use_reranker", use_reranker_default))

        if not question:
            return JSONResponse({"error": "missing question"}, status_code=400)

        # call existing answer flow
        from tools import answer_tool

        resp = await answer_tool.answer(question, limit=limit, use_reranker=use_reranker)

        # optionally filter debug fields if not requested
        if not debug and "debug" in resp:
            resp = {k: v for k, v in resp.items() if k != "debug"}

        return JSONResponse(resp)

    routes = [Route("/answer", handle_answer, methods=["POST"]) ]
    app = Starlette(debug=False, routes=routes)
    return app


if __name__ == "__main__":
    # simple CLI to run with uvicorn if available
    try:
        import uvicorn
    except Exception:
        print("uvicorn not available; install it to run the app")
    else:
        app = create_app()
        if app is None:
            print("starlette not available; cannot create app")
        else:
            uvicorn.run(app, host="127.0.0.1", port=8777)
