from typing import Any, Dict

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="agent_aggregate_and_greet",
    title="Agent: Aggregate + Greet",
    description="示例 Agent：先聚合检索再生成问候并返回汇总结果",
)
async def agent_aggregate_and_greet(
    query: str, name: str, max_results: int = 3
) -> Dict[str, Any]:
    """示例 Agent 工具：组合调用已有工具 `aggregate_search` 与 `greeting_tool`。

    返回格式：{"greeting": ..., "aggregation": {...}}
    """
    try:
        # 延迟导入以避免循环导入问题
        from tools.aggregator_tool import aggregate_search
        from tools.hello_tool import greeting_tool

        agg = await aggregate_search(query, max_results=max_results)
        greet = await greeting_tool(name)

        return {
            "greeting": greet.get("message") if isinstance(greet, dict) else greet,
            "aggregation": agg,
        }
    except Exception as e:
        raise RuntimeError(f"Agent 执行失败: {e}")
