"""聚合器工具：并发调用 providers 的 `search`，合并、去重并返回标准 Doc 列表与耗时统计。

设计要点：
- 自动发现 `providers` 包下的模块并调用其 `search(q, limit)` 函数（支持 sync 与 async）。
- 每个 provider 单独超时（默认 3s），记录耗时（ms）。
- 标准化 Doc 字段：`id,title,text,score,provider,source_url,metadata`。
- 简单去重：按标准化标题哈希（小写、去标点、空格折叠），保留最高 score。
"""
from __future__ import annotations

import asyncio
import importlib
import pkgutil
import time
import re
from typing import Any, Dict, List, Tuple

DEFAULT_PROVIDER_TIMEOUT = 3.0


def _normalize_title(title: str) -> str:
    if not title:
        return ""
    s = title.lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


async def _call_provider(module, q: str, limit: int, timeout: float) -> Tuple[str, List[Dict[str, Any]], int]:
    """Call provider.search and return (provider_name, results_list, elapsed_ms)."""
    provider_name = getattr(module, "__name__", "unknown").split(".")[-1]
    start = time.monotonic()
    try:
        func = getattr(module, "search")
        if asyncio.iscoroutinefunction(func):
            res = await asyncio.wait_for(func(q, limit), timeout=timeout)
        else:
            loop = asyncio.get_running_loop()
            res = await asyncio.wait_for(loop.run_in_executor(None, func, q, limit), timeout=timeout)
        if res is None:
            res = []
    except Exception:
        res = []
    elapsed_ms = int((time.monotonic() - start) * 1000)
    return provider_name, list(res), elapsed_ms


async def search(q: str, limit: int = 6, provider_timeout: float = DEFAULT_PROVIDER_TIMEOUT) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Search across available providers and return (docs, provider_times_ms).

    docs: list of standardized Doc dicts.
    provider_times_ms: mapping provider_name -> elapsed ms (or -1 if failed).
    """
    providers_modules = []
    try:
        import providers
        for finder, name, ispkg in pkgutil.iter_modules(providers.__path__):
            try:
                mod = importlib.import_module(f"providers.{name}")
                providers_modules.append(mod)
            except Exception:
                continue
    except Exception:
        # no providers package
        providers_modules = []

    # If none discovered, try common provider names for backwards compatibility
    if not providers_modules:
        for name in ("local_provider", "web_wiki"):
            try:
                mod = importlib.import_module(f"providers.{name}")
                providers_modules.append(mod)
            except Exception:
                continue

    tasks = [asyncio.create_task(_call_provider(m, q, limit, provider_timeout)) for m in providers_modules]
    results = []
    if tasks:
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for item in gathered:
            if isinstance(item, Exception):
                # failed call
                continue
            results.append(item)

    docs: List[Dict[str, Any]] = []
    provider_times: Dict[str, int] = {}

    for provider_name, items, elapsed in results:
        provider_times[provider_name] = elapsed
        for i, d in enumerate(items):
            doc_id = d.get("id") or f"{provider_name}:{i}"
            title = d.get("title") or d.get("id") or ""
            text = d.get("text") or d.get("snippet") or ""
            score = float(d.get("score") or d.get("relevance") or 0.5)
            source_url = d.get("source_url") or d.get("url") or None
            metadata = d.get("metadata") or {}
            docs.append({
                "id": doc_id,
                "title": title,
                "text": text,
                "score": score,
                "provider": provider_name,
                "source_url": source_url,
                "metadata": metadata,
            })

    # Simple dedupe by normalized title, keep highest score
    seen: Dict[str, Dict[str, Any]] = {}
    for d in docs:
        key = _normalize_title(d.get("title", ""))
        if not key:
            key = d["id"]
        existing = seen.get(key)
        if not existing or d["score"] > existing["score"]:
            seen[key] = d

    deduped = list(seen.values())
    deduped.sort(key=lambda x: x.get("score", 0), reverse=True)

    return deduped[:limit], provider_times


async def aggregate_search(query: str, max_results: int = 6, provider_timeout: float = DEFAULT_PROVIDER_TIMEOUT):
    """Backward-compatible wrapper used by tests and older code.

    Args:
        query: search query string
        max_results: maximum number of docs to return
        provider_timeout: per-provider timeout in seconds

    Returns:
        Tuple of (docs, provider_times)
    """
    return await search(q=query, limit=max_results, provider_timeout=provider_timeout)


def search_sync(q: str, limit: int = 6, provider_timeout: float = DEFAULT_PROVIDER_TIMEOUT):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(search(q, limit=limit, provider_timeout=provider_timeout))

