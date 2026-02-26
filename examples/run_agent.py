import asyncio
import json
import os

from tools.hello_tool import greeting_tool
from tools.aggregator_tool import aggregate_search
from tools.agent_tool import agent_aggregate_and_greet


async def run():
    print("Calling greeting_tool...")
    g = await greeting_tool("TeamMember")
    print(g)

    print("Calling aggregate_search...")
    a = await aggregate_search("示例主题", max_results=2)
    print(a)

    print("Calling agent_aggregate_and_greet...")
    ag = await agent_aggregate_and_greet("示例主题", "TeamMember", max_results=2)
    print(json.dumps(ag, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
