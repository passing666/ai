import asyncio
import logging
from typing import Any, Dict

from utils import deepseek_client

logger = logging.getLogger(__name__)


async def answer(q: str, limit: int = 4, use_reranker: bool = False) -> Dict[str, Any]:
    """High-level answer flow used by the backend.

    Steps:
    1. Call aggregator_tool.search(q, limit) to get docs (list of Doc dicts).
    2. Build RAG prompt using `prompts/rag_prompt.txt`.
    3. Call Deepseek via `deepseek_client.generate` to get generated answer.
    4. Format and return final payload with debug info.
    """
    # Import aggregator lazily to avoid cyclical imports during scaffolding
    try:
        from . import aggregator_tool
    except Exception:
        # Fallback: return helpful error for early local testing
        logger.warning("aggregator_tool not available; returning placeholder result")
        docs = [
            {"id": "local:placeholder-1", "title": "占位文档", "text": "占位文本：请实现 aggregator_tool", "score": 0.5}
        ]
        provider_times = {}
    else:
        docs, provider_times = await aggregator_tool.search(q=q, limit=limit)

    # Build a robust RAG prompt: rank+select top docs, truncate docs, include ids and titles
    def _truncate(text: str, max_chars: int = 800) -> str:
        return text if not text or len(text) <= max_chars else text[:max_chars] + "..."

    def _tokenize(s: str):
        import re

        return [t for t in re.findall(r"\w+", s.lower())]

    def _overlap_score(question: str, text: str) -> int:
        q_tokens = set(_tokenize(question))
        t_tokens = _tokenize(text)
        # simple overlap count
        return sum(1 for t in t_tokens if t in q_tokens)

    try:
        with open("prompts/rag_prompt.txt", "r", encoding="utf-8") as f:
            prompt_tmpl = f.read()
    except FileNotFoundError:
        prompt_tmpl = "Question: {q}\nDocuments:\n{docs}\nAnswer concisely."

    # Optionally use the offline reranker for better ordering.
    if use_reranker:
        try:
            from . import reranker

            selected = reranker.rerank(q, docs, top_k=limit)
        except Exception:
            # fallback to simple scoring if reranker not available
            ranked = []
            for i, d in enumerate(docs):
                base_score = float(d.get("score") or 0)
                overlap = _overlap_score(q, d.get("text") or "")
                combined = base_score + 0.1 * overlap
                ranked.append((combined, i, d))

            ranked.sort(key=lambda x: x[0], reverse=True)
            selected = [d for _, _, d in ranked][:limit]
    else:
        # compute simple relevance: provider score (if present) + keyword overlap
        ranked = []
        for i, d in enumerate(docs):
            base_score = float(d.get("score") or 0)
            overlap = _overlap_score(q, d.get("text") or "")
            combined = base_score + 0.1 * overlap
            ranked.append((combined, i, d))

        ranked.sort(key=lambda x: x[0], reverse=True)
        selected = [d for _, _, d in ranked][:limit]

    docs_entries = []
    for i, d in enumerate(selected):
        title = d.get("title") or d.get("id") or f"doc_{i+1}"
        text = _truncate(d.get("text") or "", max_chars=800)
        doc_id = d.get("id") or str(i + 1)
        docs_entries.append(f"[{i+1}] id={doc_id} title={title}\n{text}")

    docs_text = "\n\n".join(docs_entries)
    prompt = prompt_tmpl.format(q=q, docs=docs_text)

    # Call Deepseek
    try:
        import time

        t0 = time.monotonic()
        # call deepseek with a sensible timeout and retries
        ds_resp = await deepseek_client.generate(prompt, timeout=20.0, retries=2)
        deepseek_time_ms = int((time.monotonic() - t0) * 1000)
    except Exception as e:
        logger.exception("Deepseek generate failed")
        # Degraded response: return aggregated docs and note failure
        return {
            "answer": "抱歉，生成服务暂不可用；以下为聚合到的文档摘要。",
            "citations": [ {"id": d.get("id"), "url": d.get("source_url") } for d in docs ],
            "debug": {"providers_called": [], "provider_times_ms": {}, "deepseek_error": str(e)}
        }

    # Map deepseek response to expected format (assume keys 'answer' and optional 'sources')
    answer_text = ds_resp.get("answer") or ds_resp.get("text") or ""
    sources = ds_resp.get("sources") or []

    debug = {
        "providers_called": list(provider_times.keys()) if isinstance(provider_times, dict) else [],
        "provider_times_ms": provider_times if isinstance(provider_times, dict) else {},
        "deepseek_time_ms": deepseek_time_ms,
    }

    # Structured logging for provider timing and deepseek timing to assist debugging/Inspector
    try:
        import json

        logger.info(
            "provider_times",
            extra={
                "provider_times_ms": debug["provider_times_ms"],
                "deepseek_time_ms": debug["deepseek_time_ms"],
            },
        )
        # also log a compact JSON message
        logger.debug("provider_times_json: %s", json.dumps(debug, ensure_ascii=False))
    except Exception:
        logger.exception("Failed to log provider times")

    return {"answer": answer_text, "citations": sources, "debug": debug}


def answer_sync(q: str, limit: int = 4) -> Dict[str, Any]:
    return asyncio.get_event_loop().run_until_complete(answer(q, limit=limit))
