import json
import os
from typing import List, Dict, Any

try:
    from ..algo.Evaluation import calculate_normalized_scores
except (ImportError, ValueError):
    from algo.Evaluation import calculate_normalized_scores

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 建议使用绝对路径确保能找到文件
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
        # 优先取 items 键，如果没有则将整个 dict 视为单个条目包装进 list
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

    # 调用 Evaluation.py 中的向量化(余弦相似度)计算
    scores = calculate_normalized_scores(q, combined_texts)

    results = []
    for i, score in enumerate(scores):
        # 修复：只有分数大于 0 的才返回，避免返回不相关的结果
        if score <= 0:
            continue
            
        item = valid_items[i]
        doc = {
            "id": f"local:{item.get('id', '')}",
            "title": item.get("title", ""),
            "text": item.get("text", "")[:2000],
            "score": score,
            "provider": "local",
            "source_url": None,
            "metadata": item.get("metadata", {})
        }
        results.append(doc)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
