import json
import os
from typing import List, Dict, Any

try:
    from ..algo.Evaluation import calculate_normalized_scores
except (ImportError, ValueError):
    from algo.Evaluation import calculate_normalized_scores

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, "..", "..", "resources", "sample_data.json")

def search(q: str, limit: int = 10) -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        print(f"Error: file not found at {DATA_FILE}")
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {DATA_FILE}: {e}")
        return []

    # --- 修复：兼容多种 JSON 结构 ---
    if isinstance(data, list):
        items_list = data
    elif isinstance(data, dict):
        items_list = data.get("items", [data] if "id" in data else [])
    else:
        items_list = []

    if not items_list:
        return []

    valid_items = []
    combined_texts = []
    
    for item in items_list:
        if not isinstance(item, dict): continue
        title = item.get("title", "")
        text = item.get("text", "")
        
        valid_items.append(item)
        combined_texts.append(f"{title} {text}")

    scores = calculate_normalized_scores(q, combined_texts)

    results = []
    for i, score in enumerate(scores):
        if score <= 0:
            continue
            
        item = valid_items[i]
        doc = {
            "id": f"local:{item.get('id', '')}",
            "title": item.get("title", ""),
            "text": item.get("text", "")[:2000],
            "score": min( 1, score * 1.5 ),
            "provider": "local",
            "source_url": None,
            "metadata": item.get("metadata", {})
        }
        results.append(doc)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
