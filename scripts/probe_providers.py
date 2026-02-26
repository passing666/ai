import asyncio
from tools import aggregator_tool


async def main():
    docs, provider_times = await aggregator_tool.search("示例", limit=5)
    print("provider_times:", provider_times)
    print("docs_count:", len(docs))
    for d in docs:
        print("-", d.get("id"), d.get("title")[:40])


if __name__ == "__main__":
    asyncio.run(main())
