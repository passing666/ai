import json
import os
from typing import List, Dict, Any

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "sample_data.json")


def _load_sample_items() -> List[Dict[str, Any]]:
    try:
        p = os.path.abspath(DATA_PATH)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("items", [])
    except Exception:
        return []


def search(q: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Simple synchronous local provider: keyword match on title and return docs."""
    items = _load_sample_items()
    q_low = (q or "").lower()
    results: List[Dict[str, Any]] = []
    for it in items:
        title = str(it.get("title", ""))
        text = str(it.get("value", ""))
        score = 1.0 if q_low in title.lower() else 0.4
        results.append({
            "id": f"local:{it.get('id')}",
            "title": title,
            "text": text,
            "score": score,
            "source_url": None,
            "metadata": {},
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
