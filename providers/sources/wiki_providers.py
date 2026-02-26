import urllib.parse
import re
from typing import List, Dict, Any
try:
    from ..algo.Evaluation import calculate_normalized_scores
except (ImportError, ValueError):
    from algo.Evaluation import calculate_normalized_scores

try:
    import requests
except ImportError:
    requests = None


def search(q: str, limit: int = 10) -> List[Dict[str, Any]]:
    if requests is None:
        print("Error: 'requests' library is not installed.")
        return []

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": q,
        "format": "json",
        "utf8": 1,
        "srlimit": limit
    }

    try:
        headers = {
            "User-Agent": "AIAgentProject/1.0 (https://github.com/passing666/ai; vacbo9527@gmail.com)"
        }
        response = requests.get(url, params=params, headers=headers, timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Warning: web_wiki provider failed: {e}")
        return []

    search_results = data.get("query", {}).get("search", [])
    if not search_results:
        return []

    valid_items = []
    combined_texts = []

    for item in search_results:
        title = item.get("title", "")
        raw_snippet = item.get("snippet", "")
        clean_text = re.sub(r'<[^>]+>', '', raw_snippet)
        
        valid_items.append({
            "pageid": item.get("pageid"),
            "title": title,
            "text": clean_text
        })
        combined_texts.append(title + " " + clean_text)

    scores = calculate_normalized_scores(q, combined_texts)

    results = []
    for i, score in enumerate(scores):
        if score <= 0:
            continue
            
        item = valid_items[i]
        title = item["title"]
        
        # 2. 修改原始来源 URL 为英文版地址
        source_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"
        
        doc = {
            "id": f"web_wiki:{item['pageid']}",
            "title": title,
            "text": item["text"][:2000],
            "score": score,
            "provider": "web_wiki",
            "source_url": source_url,
            "metadata": {}
        }
        results.append(doc)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
