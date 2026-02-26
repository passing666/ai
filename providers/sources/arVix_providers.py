import urllib.parse
import re
import xml.etree.ElementTree as ET
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

    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{q}",
        "start": 0,
        "max_results": limit
    }

    try:
        headers = {
            "User-Agent": "AIAgentProject/1.0 (https://github.com/passing666/ai)"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10.0)
        response.raise_for_status()
        xml_data = response.text
    except Exception as e:
        print(f"Warning: arxiv provider failed: {e}")
        return []

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"Error parsing arXiv XML: {e}")
        return []

    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    entries = root.findall('atom:entry', ns)
    if not entries:
        return []

    valid_items = []
    combined_texts = []

    for entry in entries:
        # 定义一个内部辅助函数，安全提取 XML 文本
        def get_node_text(node, tag):
            found = node.find(tag, ns)
            return found.text if (found is not None and found.text) else ""

        # 1. 安全提取各字段
        title = get_node_text(entry, 'atom:title')
        title = re.sub(r'\s+', ' ', title).strip()
        
        summary = get_node_text(entry, 'atom:summary')
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        paper_id_url = get_node_text(entry, 'atom:id').strip()
        
        # 如果连 URL 都没有，这一条结果就没意义，跳过
        if not paper_id_url:
            continue

        paper_id = paper_id_url.split('/')[-1]

        valid_items.append({
            "id": paper_id,
            "title": title,
            "text": summary,
            "source_url": paper_id_url
        })
        combined_texts.append(f"{title} {summary}")

    scores = calculate_normalized_scores(q, combined_texts)

    results = []
    for i, score in enumerate(scores):
        if score <= 0:
            continue
            
        item = valid_items[i]
        
        doc = {
            "id": f"arxiv:{item['id']}",
            "title": item["title"],
            "text": item["text"][:2000], # 限制长度
            "score": score,
            "provider": "arxiv",
            "source_url": item["source_url"],
            "metadata": {
                # 可以根据需要添加作者等额外信息
            }
        }
        results.append(doc)

    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
