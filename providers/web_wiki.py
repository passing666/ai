import asyncio
from typing import List, Dict, Any


async def search(q: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Stub async provider that simulates a web wiki provider.

    Returns a small list of synthesized docs to allow E2E testing when
    external network-based providers are not available.
    """
    await asyncio.sleep(0.01)
    q_low = (q or "").strip()
    if not q_low:
        return []
    return [
        {
            "id": f"wiki:{q_low}:1",
            "title": f"Wiki 关于 {q_low}",
            "text": f"这是关于 {q_low} 的合成条目，用于本地测试。",
            "score": 0.6,
            "source_url": None,
            "metadata": {},
        }
    ][:limit]
