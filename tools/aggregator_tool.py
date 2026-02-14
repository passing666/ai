import os
from typing import Dict, Any

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="aggregate_search",
    title="Aggregate Search",
    description="聚合API查询封装（占位实现）",
)
async def aggregate_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """示例聚合 API 封装。

    如果环境变量 `AGGREGATION_API_URL` 未设置，则返回模拟数据。
    否则尝试使用 `requests` POST 请求到该 URL，传入 JSON: {"query":..., "max_results":...}
    """
    api_url = os.getenv("AGGREGATION_API_URL")
    api_key = os.getenv("AGGREGATION_API_KEY")

    if not api_url:
        # 返回模拟结果，便于本地开发与测试
        results = [
            {"title": f"示例结果 {i+1}", "snippet": f"这是与 '{query}' 相关的示例摘要 {i+1}."}
            for i in range(max_results)
        ]
        return {"source": "mock", "query": query, "results": results}

    try:
        import requests

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        resp = requests.post(api_url, json={"query": query, "max_results": max_results}, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"聚合API请求失败: {e}")
