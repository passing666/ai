from __init__ import unified_search

def run_demo():
    query = "什么是卷积神经网络"
    print(f"--- 正在搜索: '{query}' ---")

    results = unified_search(query, limit=10)

    if not results:
        print("未找到相关结果。")
        return

    for i, doc in enumerate(results, 5):
        print(f"\n[{i}] 相似度得分: {doc['score']:.2f} | 来源: {doc['provider']}")
        print(f"标题: {doc['title']}")
        snippet = doc['text'][:1000].replace('\n', ' ')
        print(f"内容: {snippet}...")
        
        if doc.get('source_url'):
            print(f"链接: {doc['source_url']}")

if __name__ == "__main__":
    run_demo()
