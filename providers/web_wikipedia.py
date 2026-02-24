"""Wikipedia provider using MediaWiki API (async).

This provider is best-effort: if `httpx` is not available or network fails,
it returns an empty list so local testing remains deterministic.
"""
from __future__ import annotations

from typing import List, Dict, Any


async def search(q: str, limit: int = 5) -> List[Dict[str, Any]]:
    if not q:
        return []
    try:
        import httpx
    except Exception:
        # httpx not installed in the environment used for tests; gracefully degrade
        return []

    endpoint = "https://zh.wikipedia.org/w/api.php"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # search for pages
            params = {
                "action": "query",
                "list": "search",
                "srsearch": q,
                "srlimit": max(1, limit),
                "format": "json",
            }
            r = await client.get(endpoint, params=params)
            r.raise_for_status()
            js = r.json()
            hits = js.get("query", {}).get("search", [])
            if not hits:
                return []
            pageids = [str(h.get("pageid")) for h in hits[:limit]]

            # fetch extracts for pageids
            params2 = {
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "exintro": 1,
                "pageids": "|".join(pageids),
                "format": "json",
            }
            r2 = await client.get(endpoint, params=params2)
            r2.raise_for_status()
            js2 = r2.json()
            pages = js2.get("query", {}).get("pages", {})

            out = []
            for pid in pageids:
                p = pages.get(pid)
                if not p:
                    continue
                title = p.get("title")
                extract = p.get("extract") or ""
                out.append({
                    "id": f"wikipedia:{pid}",
                    "title": title,
                    "text": extract,
                    "score": 0.7,
                    "source_url": f"https://zh.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "metadata": {},
                })
            return out[:limit]
    except Exception:
        return []
