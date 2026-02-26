import asyncio

from tools.hello_tool import get_server_config, greeting_tool
from tools.aggregator_tool import aggregate_search
from tools.agent_tool import agent_aggregate_and_greet


async def main():
    try:
        res1 = await get_server_config("server.name")
        print("\n=== get_server_config ===")
        print(res1)

        res2 = await greeting_tool("Alice")
        print("\n=== greeting_tool ===")
        print(res2)

        res3 = await aggregate_search("测试查询", max_results=2)
        print("\n=== aggregate_search ===")
        print(res3)

        res4 = await agent_aggregate_and_greet("论文主题", "Bob", max_results=2)
        print("\n=== agent_aggregate_and_greet ===")
        print(res4)
    except Exception as e:
        print("Error during calls:", e)


if __name__ == "__main__":
    asyncio.run(main())
