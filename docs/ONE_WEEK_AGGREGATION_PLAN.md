# 一周内可交付的聚合 API 计划（详细说明）

本文档为一周（7 天）内可实现的聚合 API 选项的详细说明，针对每个选项列出：
- 需要聚合的具体 API/数据源（哪些“API”会被聚合）
- 功能/用途（用户可见的效果）
- 推荐的返回字段（统一 schema 要点）
- 需要的提示词（可直接复制到 `prompts/`）——含系统指令与示例输入，通俗易懂
- Inspector 调试要点（如何在 `MCP Inspector` 演示）

注：本计划优先聚合“易实现且有现实意义”的 API，便于演示与评分。

----

## 选项 A：Local 文档聚合（强烈推荐，闭环演示）

1) 聚合哪些 API / 数据源
- 本地静态文档（`resources/` 下的 JSON、Markdown、TXT、`README.md`）
- 项目内注册为 `@mcp.resource` 的资源（若存在）

2) 做什么（功能）
- 一次查询检索本地所有文档，返回统一格式的片段（带来源与置信度）。
- 支持查看原文（`/retrieve`），支持在 Inspector 演示整个流程。

3) 推荐返回字段（最小集合）
- `id, source='local', title, snippet/text, path, fetched_at, language, score, provenance`。

4) 提示词（放入 `prompts/aggregator_provider.txt`）
- System（指令）: 你是本地文档检索适配器。输入 JSON: {"query":"...","limit":N,"filters":{...}}。返回 JSON 数组，元素字段：`id`、`title`、`text`、`path`、`timestamp`、`language`、`score`。仅输出 JSON 数组，不要添加其他文字。
- User（示例）: {"query":"如何启动 MCP Server","limit":5,"filters":{"language":"zh"}}

5) Inspector 调试要点
- 在 Inspector 中先调用 `GET /providers` 验证 local provider 已注册；再 POST `/aggregate_search` 查看返回，最后对某条结果调用 `POST /retrieve` 查看全文。

### AI 模型与算法应用（本选项）
- 可应用模型：
  - 关键词检索（BM25）：快速、无需额外模型，适合小数据集（难度：Easy）。
  - 本地 Embedding（sentence-transformers）+ ANN（FAISS/hnswlib）：用语义检索替代或补充 BM25（难度：Moderate）。
- 实现步骤（建议）：
  1. 先实现 BM25 或简单全文搜索作为 baseline（whoosh 或现成文本搜索）。
  2. 将本地文档切片（chunking），对每片生成 embedding（`all-MiniLM-L6-v2`），批量存入 FAISS 索引。
  3. `POST /aggregate_search` 支持 `mode` 参数（`bm25` 或 `embed`），便于对比效果。
  4. 在 Inspector 中对比两种模式的结果并记录召回/相关性差异。
- 示例提示词（用于 reranker/RAG 流程）：
  - Embedding provider（adapter）: "你是检索适配器，接收 {query,limit} 返回 JSON 数组..."
  - 若后续做 RAG：使用 `prompts/aggregator_rag.txt` 中的 RAG 模板。

### 示例（本地文档聚合）

- 场景：想快速找出项目 README 中的启动命令。

- 请求（Inspector POST `/aggregate_search`）:

  {
    "query": "如何启动 MCP Server",
    "limit": 5,
    "sources": ["local"]
  }

- 返回（简化示例）:

  [
    {
      "id": "local:readme:1",
      "title": "README",
      "snippet": "激活 .venv 后运行 uv run server.py",
      "source": "local",
      "normalized_score": 0.95
    }
  ]

- 操作：在 Inspector 点击该结果，再调用 `POST /retrieve` 查看完整 README，以核验 snippet 的出处。


----

## 选项 B：Providers 列表与健康检查（非常容易，辅助演示）

1) 聚合哪些 API / 数据源
- 当前服务内注册的所有 provider（local, tool adapters, external adapters）

2) 做什么（功能）
- 列出 provider 能力（search/retrieve/embeddings），显示状态/延迟，便于 Inspector 验证与演示。

3) 推荐返回字段
- `provider_id, name, capabilities:[...], status, last_seen, latency_ms`。

4) 提示词（无需复杂推理，直接由服务端生成）
- 无需 LLM；provider 自述由注册逻辑输出。若用 prompt 生成文档说明，可用：
  System: 请基于注册信息生成 provider 可读说明（name,capabilities,status）。仅输出 JSON。

5) Inspector 调试要点
- 直接调用 `GET /providers`，检查每个 provider 的 `capabilities` 是否包括 `search` 或 `retrieve`，并用 `/retrieve` 单独验证一个 provider。

### AI 模型与算法应用（本选项）
- 可应用模型：
  - 无需深度学习：此选项主要用于元信息展示（难度：Very Easy）。
  - 若需要自动生成 provider 说明，可用小型 LLM 或模板（如 GPT-family 或本地轻量模型）生成 human-friendly 描述（难度：Easy）。
- 实现步骤（建议）：
  1. provider 在注册时上报能力标签（search/retrieve/embeddings/generate）。
  2. 若要自动生成说明，收集 provider 元字段并调用 `generate()` adapter 生成简短描述。
  3. 在 Inspector 中展示 latency、status；对异常 provider 触发提示（例如自动生成的错误摘要）。
- 示例提示词（用于生成 provider 描述）：
  - System: "基于以下 provider 元信息，生成一段不超过50字的说明，说明其能力和注意事项。返回 JSON {name,summary}." 

### 示例（Providers 列表与健康检查）

- 场景：演示有两个 provider 注册：`local_docs` 与 `web_wiki`，并查看状态。

- 请求（Inspector GET `/providers`）:

  返回（示例）:

  [
    {"provider_id":"local_docs","name":"Local Docs","capabilities":["search","retrieve"],"status":"ok","latency_ms":12},
    {"provider_id":"web_wiki","name":"Web Wiki Adapter","capabilities":["search"],"status":"degraded","latency_ms":450}
  ]

- 操作：在 Inspector 中看到 `web_wiki` 状态为 `degraded` 后，单独调用其 `/retrieve` 或查看 `raw_response`，排查超时或格式错误。


----

## 选项 C：统一入口 — `/aggregate_search`（核心入口，A 的延伸）

1) 聚合哪些 API / 数据源
- 同时并行调用：Local provider、MCP Resource、MCP Tool（或 External API Adapter）。

2) 做什么（功能）
- 把多个 provider 的返回合并为统一列表，去重、归一化分数，返回带 provenance 的结果供前端/LLM 使用。

3) 推荐返回字段
- `id, title, snippet, source, normalized_score, provenance:[{source,score}], timestamp`。

4) 提示词（放入 `prompts/aggregator_search.txt`）
- System: 你是聚合控制器。输入为多个 provider 返回的 doc 列表，每个 doc 含 `id,title,text,source,score,url`。请：
  1) 合并这些列表为统一数组；
  2) 执行简单去重（相同 id 或文本高度重复）；
  3) 为每条记录生成 `provenance`（来源数组）和 `normalized_score`（0-1）；
  输出：JSON 数组 [{id,title,snippet,source,normalized_score,provenance,timestamp}]。仅输出 JSON。
- User（示例）: {"providers_responses": [...]}（将 provider 返回附上）

5) Inspector 调试要点
- 在 Inspector 内发送 POST `/aggregate_search`。若出现 `partial: true` 或 `errors` 字段，说明某 provider 超时/失败，按错误排查单独调用该 provider。

### AI 模型与算法应用（本选项）
- 可应用模型：
  - 结合 BM25 + Embedding（hybrid retrieval）：先 BM25 快速召回，再用 embedding 精选（难度：Moderate）。
  - 归一化分数策略：用简单的 min-max 或学习到的线性加权（难度：Easy→Moderate）。
  - 去重与合并可用文本相似度（cosine）或 fuzzy matching（难度：Easy）。
- 实现步骤（建议）：
  1. 设计统一内部 Doc schema，确保每 provider 返回可映射字段。
  2. 实现 hybrid retriever：当 `mode=hybrid` 时，先 BM25 召回 top-N，再对这 top-N 用 embedding 相似度重排序并计算 normalized_score。
  3. 去重：对返回文本计算 cosine 相似度，阈值合并并合并 provenance 列表。
  4. 在合并层记录 metrics（召回数、去重率、provider latency）以便调优。
- 示例提示词（合并层可能使用 LLM 时）：
  - System: "你是合并控制器，接收多个 provider 的 doc 列表，执行去重与归一化得分，返回 JSON 数组..."（见 `prompts/aggregator_search.txt`）

### RAG 与 C 的结合（实务指南）

RAG（检索增强生成）可以直接基于 `C` 的输出工作：把 `POST /aggregate_search` 的 top-K 文档作为检索上下文，经过可选的 `/rerank` 精排后输入 RAG prompt 调用 LLM 生成答案并返回 `citations`。下面是可复制的流程、要点与示例。

- 推荐流程（具体实现）
  1. 调用 `POST /aggregate_search` 获取 candidates（每项包含 `id,text,provenance,score`）。
  2. （可选）调用 `POST /rerank` 对 candidates 做精排，减少噪声（例如 top-50 -> top-10）。
  3. 按 token 预算选择 top-N（例如 N=3），若片段过长先做摘要或提取要点。
  4. 构造 RAG prompt（使用 `prompts/aggregator_rag.txt`），把选中文档作为 context 插入，调用 LLM（本地或云）。
  5. 返回 JSON 包含 `answer, used_doc_ids, citations`，并在 `citations` 中保留 `url`/`provenance` 供 Inspector 跳转或复核。

- 工程要点
  - Token 预算：计算选中文档与 prompt 的 token 总量，优先选择高 `normalized_score` 文档并摘要长文。
  - 缓存：对相同 query 使用 query-hash 缓存 RAG 输出以节省成本与延迟。
  ️- 可靠性：记录 LLM 请求的 token 用量与费用指标，异常时退回纯检索结果并在响应中标注 `rag_error`。
  - 可审计性：`citations` 必须包含原始 provider id 与定位信息（path/url/timestamp），便于 `POST /retrieve` 验证。

- 示例交互（Inspector 可直接调用）
  1) POST `/aggregate_search` 请求体：
  {
    "query":"如何启动 MCP Server",
    "limit":20,
    "sources":["local","web_wiki"]
  }

  2) 取返回 top-3 文档，POST `/rag_answer` 请求体：
  {
    "query":"如何启动 MCP Server",
    "documents":[
      {"id":"local:readme:1","text":"激活 .venv 后运行 uv run server.py"},
      {"id":"web:wiki:123","text":"使用 mcp dev server.py 可以在 Inspector 中调试"},
      {"id":"local:guide:2","text":"为 windows 用户，先运行 .venv\\Scripts\\Activate.ps1"}
    ]
  }

  返回示例见 RAG 小节示例（包含 `citations`），Inspector 可以逐项 `POST /retrieve` 校验出处。

### 推荐易用且免费的外部 API（用于作为 provider）

以下 API 无需复杂付费流程或可匿名访问，适合课堂演示与快速集成：

- Wikipedia / MediaWiki API（百科）
  - 特点：免费、内容丰富、无需 API key（有访问频率限制）。
  - 简单调用示例（curl）：
    ```bash
    curl "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&format=json&exintro=&titles=Artificial%20intelligence"
    ```

- DuckDuckGo Instant Answer API（简洁答案）
  - 特点：无需 key，返回摘要式答案适合短问答。
  - 调用示例：
    ```bash
    curl "https://api.duckduckgo.com/?q=python+list+comprehension&format=json"
    ```

- Open Library API（图书元数据）
  - 用途：查书信息、参考资料示例。
  - 示例：
    ```bash
    curl "https://openlibrary.org/search.json?q=computer+science"
    ```

- arXiv API（学术检索）
  - 用途：抓取论文摘要，适合课程/研究类示例。
  - 示例：
    ```bash
    curl "http://export.arxiv.org/api/query?search_query=all:transformers&start=0&max_results=5"
    ```

- Crossref API（学术元数据）
  - 示例：
    ```bash
    curl "https://api.crossref.org/works?query=neural%20networks"
    ```

这些外部源可作为 `web_wiki` 或 `arxiv` provider 的实现示例，返回内容在 provider 端做清洗并映射为内部 Doc schema（id,title,text,url,timestamp,score）。

### provider 适配器实现建议（示例）

每个外部 API 实现为 provider adapter，职责为：调用外部 API、解析 response、映射到 Doc schema、返回标准 JSON 数组。

示例伪代码：
```python
def web_wiki_fetch(query, limit=5):
    resp = requests.get(WIKI_API_URL, params={...})
    # 解析 extract 字段
    docs = []
    for item in parsed:
        docs.append({
            'id': f'web:wiki:{item_id}',
            'title': item_title,
            'text': item_extract,
            'url': item_url,
            'timestamp': item_timestamp,
            'score': compute_score(...)
        })
    return docs
```

映射要点：始终返回 `id, title, text, url, timestamp, score, source`，便于聚合层统一处理与展示。

### 示例（/aggregate_search 聚合示例）

- 场景：同时从 `local` 和 `web_wiki` 聚合关于“如何运行 MCP Server”的信息。

- 请求（Inspector POST `/aggregate_search`）:

  {
    "query": "如何运行 MCP Server",
    "limit": 5,
    "sources": ["local","web_wiki"]
  }

- 返回（合并后示例）:

  [
    {
      "id":"local:readme:1",
      "title":"README",
      "snippet":"激活 .venv 后执行 uv run server.py",
      "source":"local",
      "normalized_score":0.94,
      "provenance":[{"source":"local","score":0.9}]
    },
    {
      "id":"web:wiki:123",
      "title":"MCP Server 文档",
      "snippet":"使用 mcp dev server.py 可在 Inspector 中调试",
      "source":"web_wiki",
      "normalized_score":0.82,
      "provenance":[{"source":"web_wiki","score":0.82}]
    }
  ]

- 操作：若 `provenance` 显示多个来源相似，Inspector 中可选择某条调用 `POST /retrieve` 核验原文。


----

## 选项 D：简单 Rerank（用 LLM 或轻量模型对 top-k 排序）

1) 聚合哪些 API / 数据源
- 来源仍由 `/aggregate_search` 提供（Top-K 候选）。

2) 做什么（功能）
- 使用 LLM 或规则对候选进行评分/重排序，并给出简短理由（便于演示与审计）。

3) 推荐返回字段
- `candidate_id, original_score, rerank_score, reason`。

4) 提示词（放入 `prompts/aggregator_rerank.txt`）
- System: 你是相关性评分器。输入包含 `query`（字符串）与 `candidates`（数组，每项包含 `id` 和 `text`）。请为每个候选按相关性输出 `{ "id":"...","score":0-100,"reason":"一句话理由" }`，并按 `score` 降序返回数组。仅输出 JSON。
- User（示例）: {"query":"如何启动 MCP Server","candidates":[{"id":"local:1","text":"..."}, ...]}

5) Inspector 调试要点
- 先调用 `/aggregate_search` 得到候选，再把候选及 query 发给 `/rerank`。观察排序与 `reason` 字段，以评估 reranker 有无实际提升。

### AI 模型与算法应用（本选项）
- 可应用模型：
  - 轻量启发式规则（关键词覆盖、时间优先、来源可信度）：快速实现（难度：Easy）。
  - Cross-encoder（sentence-transformers cross-encoder）：精排 top-K（准确但慢，难度：Moderate）。
  - LLM scoring（prompt-based scoring）：在无法训练 cross-encoder 时使用（成本与延迟较高，难度：Moderate）。
- 实现步骤（建议）：
  1. 把 `/aggregate_search` 的 top-K 取出，按需求限制数量（如 top-20）。
  2. 若使用 cross-encoder：批量构造 (query, candidate) 对进行评分并返回排序；若使用 LLM，则构造评分 prompt（见 `prompts/aggregator_rerank.txt`）。
  3. 将 rerank_score 与原始 score 一并返回，并在 UI/Inspector 展示 `reason` 字段。
  4. 记录 reranker 的效果（使得 top-1/3 的准确率提升多少），便于后续模型选择。
- 示例提示词（reranker）见 `prompts/aggregator_rerank.txt`。

### 示例（Rerank 示例）

- 场景：`/aggregate_search` 返回两个候选，想让 reranker 选出更准确的一条。

- 输入（POST `/rerank`）:

  {
    "query":"如何启动 MCP Server",
    "candidates":[
      {"id":"local:1","text":"激活 .venv 后运行 uv run server.py"},
      {"id":"web:2","text":"在某些环境中请先运行 mcp dev server.py"}
    ]
  }

- 返回（简化示例）:

  [
    {"id":"local:1","score":95,"reason":"直接来自项目 README，最权威"},
    {"id":"web:2","score":80,"reason":"环境依赖不同，需额外步骤"}
  ]

- 操作：在 Inspector 中对比原始排序和 rerank 后顺序，检查 `reason` 帮助定位为何被提升或下降。


----

## 选项 E：RAG（检索增强生成）

1) 聚合哪些 API / 数据源
- `/aggregate_search` 输出的 top-k 文档，可能再经 `/rerank` 精选。

2) 做什么（功能）
- 把检索到的片段作为上下文注入 LLM，生成带引用的回答（并在文本中标注 `[source:id]`），适合教学演示“可复查”的 LLM 回答。

3) 推荐返回字段
- `answer, used_doc_ids, citations:[{id,excerpt,source,url}], next_steps(optional)`。

4) 提示词（放入 `prompts/aggregator_rag.txt`）
- System: 你是一个回答生成器，只能使用下面提供的文档片段回答问题。返回 JSON：
  {"answer":"...","used_doc_ids":[...],"citations":[{"id":"...","excerpt":"...","source":"...","url":"..."}],"next_steps":[]}。
  在答案中引用文档时，请在句尾用 `[source:id]` 标注。若无法回答，请将 `answer` 设为 "无法从已检索文档得到答案" 并在 `next_steps` 提供 1-2 条检索建议。
- User（示例）: {"query":"MCP Server 如何运行？","documents":[{id,text},...]}

5) Inspector 调试要点
- 在 Inspector 里先运行 `/aggregate_search`，将返回 top-k 文档与 query 一并发给 `/rag_answer`。检查 `citations` 是否正确且能追溯到 `retrieve` 的原文。

### AI 模型与算法应用（本选项）
- 可应用模型：
  - LLM（OpenAI 或本地 LLM）：用于将检索片段编码入 prompt 并生成答案（难度：Moderate，若使用云服务则涉及成本）。
  - 摘要模型或长文本摘要策略：若片段过大，先用摘要模型压缩再输入 LLM（难度：Moderate）。
  - Citation extraction：可用简单规则或小模型从片段中抽取引用摘录（难度：Easy）。
- 实现步骤（建议）：
  1. 从 `/aggregate_search` 得到 top-k 文档，按 token 预算选取能放入 prompt 的片段（优先长且高 score 的片段或用摘要代替）。
  2. 构造 RAG prompt（使用 `prompts/aggregator_rag.txt`），并调用 LLM 生成 JSON 化的答案与 `citations`。
  3. 验证 `citations` 可通过 `/retrieve` 回溯；若发现不一致，增加调试日志并在 Inspector 中显示 conflict/警告。
  4. 控制 token 成本：对常见 query 做缓存，对重复 query 直接返回缓存答案。
- 示例提示词（RAG）见 `prompts/aggregator_rag.txt`。

### 示例（RAG 示例）

- 场景：用户问“如何在本项目中运行 MCP Server？”，希望得到带出处的简短步骤。

- 输入（POST `/rag_answer`）:

  {
    "query":"如何在本项目中运行 MCP Server？",
    "documents":[
      {"id":"local:readme:1","text":"激活 .venv 后运行 uv run server.py"},
      {"id":"web:wiki:123","text":"使用 mcp dev server.py 可以在 Inspector 中调试"}
    ]
  }

- 返回（示例）:

  {
    "answer":"在本项目中，先激活虚拟环境，然后运行 `uv run server.py` 启动服务器。[source:local:readme:1] 若要用 Inspector 进行交互式调试，可运行 `mcp dev server.py` 并在 Inspector 选择 sse 或 stdio 连接。[source:web:wiki:123]",
    "used_doc_ids":["local:readme:1","web:wiki:123"],
    "citations":[
      {"id":"local:readme:1","excerpt":"激活 .venv 后运行 uv run server.py","source":"local","url":"file://./README.md"},
      {"id":"web:wiki:123","excerpt":"使用 mcp dev server.py 可以在 Inspector 中调试","source":"web_wiki","url":"https://example.org/mcp-docs"}
    ]
  }

- 操作：在 Inspector 中查看 `citations` 列表并用 `POST /retrieve` 验证每个引用的原文是否一致。


----

## 选项 F（可选，超出一周但值得了解）：外部 API 聚合与向量检索

1) 聚合哪些 API
- 维基百科 / 公共 REST API、学术检索 API（如 arXiv）和 embedding 服务（OpenAI, local embedder）。

2) 做什么（功能）
- 扩展知识覆盖，提供最新/外部事实来源；向量检索提升语义匹配能力。

3) 关键提示词样板
- External provider adapter: 类似 `aggregator_provider.txt` 的系统指令，但需在适配器中管理 API keys（PPT 建议使用 `sops` 管理 secrets）。
- Embedding pipeline: 不是直接 prompt，而是对文本生成 embedding 并存入向量索引；检索步骤与 `/aggregate_search` 集成。

4) Inspector 调试要点
- 验证外部 provider 返回的 `url`/`license` 字段；若为 embedding 相关，确认 `embedding_vector` 字段存在或返回清晰错误。

### AI 模型与算法应用（本选项）
- 可应用模型：
  - Embedding 服务（OpenAI 或本地 sentence-transformers）用于语义检索（难度：Moderate）。
  - ANN 索引（FAISS/hnswlib）结合 Bi-encoder 做大规模检索（难度：Moderate→Hard）。
  - Cross-encoder 或 LLM 做 top-k 精排与复核（难度：Moderate）。
  - 对外部 API 的结果可做信源可信度评分（规则或模型）（难度：Moderate）。
- 实现步骤（建议）：
  1. 设计外部 provider adapter，确保返回有 `license`、`url`、`timestamp` 字段用于合规性检查。
  2. 建立 embedding pipeline：文本分片 -> embed -> 入索引（FAISS/hnswlib）。
  3. 定期同步/刷新索引，处理外部数据更新与去重。
  4. 在聚合层合并外部结果时增加 `source_weight`（基于信誉/延迟/license 调整分数）。
- Inspector 调试要点补充：
  - 提供示例 payload 来测试外部 provider 的速率限制与错误场景；在 Inspector 中显示 `raw_response` 以便审查。

### 示例（外部 API 与向量检索）

- 场景：聚合维基百科和本地文档来回答“某算法概念”的定义，并使用向量检索找到语义相关片段。

- 流程：
  1. 从 `web_wiki` 拉取相关文章并入库；对本地与 web 文档做相同分片与 embedding。
  2. 对用户 query 生成 embedding，在 FAISS 中检索 top-10（返回距离/相似度）。
  3. 把 top-10 发给 reranker（cross-encoder）得到最终排序，并用 RAG 生成答案。

- 示例搜索返回（简化）:
  [
    {"id":"wiki:567","title":"算法X","snippet":"算法X 是...","similarity":0.87,"source":"web_wiki"},
    {"id":"local:notes:12","title":"讲义片段","snippet":"在课程中，算法X 应用...","similarity":0.79,"source":"local"}
  ]

- 操作：在 Inspector 中测试 embedding 检索接口（`POST /embed_search`），查看 `similarity`，再用 `/retrieve` 核验原文并最终调用 `/rag_answer` 来生成带引用的答案。


----

## 附：示例 Inspector 演示流程（基于 PPT 要求）
1. 启动服务：
```powershell
.venv\\Scripts\\Activate.ps1
pip install -e .
uv run server.py
```
2. 打开 `mcp dev` / MCP Inspector，选择 `sse` 或 `stdio` 并 Connect。
3. 调用 `GET /providers` 验证 provider 注册。
4. 调用 `POST /aggregate_search`（示例 payload 已在 `examples/` 中准备）。
5. 对返回结果调用 `POST /retrieve` 查看原文；对 top-k 调用 `POST /rerank` 与 `POST /rag_answer` 演示重排序与引用生成。

----

## 文件建议（我会/已生成）
- `prompts/aggregator_provider.txt`（provider 调用规范）
- `prompts/aggregator_search.txt`（聚合控制器）
- `prompts/aggregator_rerank.txt`（reranker）
- `prompts/aggregator_rag.txt`（RAG 汇总）
- `tools/aggregator_tool.py`（provider 接口与 local provider 骨架）

----

如果你同意，我可以现在把这些 prompts 文件写入仓库并生成 `tools/aggregator_tool.py` 的骨架实现（包含 Local provider、`/aggregate_search`、`/providers`、`/retrieve`），然后在本地用 MCP Inspector 做演示。请回复“开始”或说明优先级调整。

----

## 附录：集成人工智能模型与算法（补充说明）

下面把如何在上述一周计划各选项中加入人工智能模型与算法（embedding、rerank、RAG、向量检索等）拆成可执行步骤、所需依赖、示例命令与最小代码片段，便于直接落实到项目中。

1) 目标映射（把模型功能映射到选项）
- Local 文档聚合：可先用 BM25（快速）或 embedding 检索提高语义召回。
- `/aggregate_search`：在合并层使用 normalized_score；若启用 embedding，则把向量距离合成到 normalized_score。
- `/rerank`：使用 cross-encoder 或 LLM scoring 对 top-K 重排并生成 `reason`。
- `/rag_answer`：用 LLM 将 top-K 文档作为上下文生成带引用的回答。

2) 必要依赖与安装（建议）
```powershell
# 虚拟环境（Windows）
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
# 本地 embedding + rerank
pip install sentence-transformers faiss-cpu hnswlib
# LLM 客户端（若使用 OpenAI）
pip install openai
``` 
注意：Windows 下 `faiss-cpu` 与 `hnswlib` 安装要看 Python 版本，若安装失败可改用轻量库或在 Linux 容器中运行。

3) model adapter（建议放 `tools/model_adapters.py`）
- 统一接口示例：
```python
from typing import List

class ModelAdapter:
    def embed(self, texts: List[str]) -> List[List[float]]: ...
    def generate(self, messages: List[dict], **kwargs) -> dict: ...
    def score(self, query: str, candidates: List[str]) -> List[float]: ...

# local embedding 示例（sentence-transformers）
from sentence_transformers import SentenceTransformer
_EMB_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
def embed(texts):
    return _EMB_MODEL.encode(texts, convert_to_numpy=True).tolist()
```

4) 向量索引（FAISS 简单示例）
```python
import faiss, numpy as np
embs = np.array(embed(text_list), dtype='float32')
dim = embs.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embs)
# 搜索
D, I = index.search(np.array([query_emb], dtype='float32'), k=10)
``` 

5) 简单 reranker（LLM scoring）提示词示例
- System: 你是相关性评分器。输入为 {"query":"...","candidates":[{"id":"...","text":"..."}] }。
  请为每个候选返回 {"id":"...","score":0-100,"reason":"一句话理由"}，仅输出 JSON 数组。

6) RAG prompt（生成答案并引用）示例
- System: 你只能使用下面的文档片段回答问题，答案中必须在句尾用 [source:id] 标注证据。返回 JSON {"answer":"...","used_doc_ids":[...],"citations":[{...}]}. 若无法回答，answer 为 "无法从已检索文档得到答案" 并提供 next_steps。

7) 运行与调试命令（快速演示）
```powershell
# 启动服务
.venv\Scripts\Activate.ps1
pip install -e .
uv run server.py
# 在另一个终端启动 Inspector
mcp dev server.py
``` 

8) 一周内实现建议（任务拆解）
- Day1: 准备依赖、实现 `tools/model_adapters.py`（embed + generate skeleton），在 `resources/` 做文本分片。
- Day2: 搭建 embedding pipeline、生成 embeddings 并构建 FAISS 索引（small dataset）。
- Day3: 实现 `/aggregate_search` 支持 embedding 检索与 BM25 备用；写 Inspector 示例请求。
- Day4: 实现 `/retrieve` 与 `GET /providers`；完善 provenance 字段与错误处理。
- Day5: 实现 `/rerank`（调用 LLM 或 cross-encoder），集成提示词并测试排序效果。
- Day6: 实现 `/rag_answer`（把 top-k 文档注入 prompt 生成带引用答案），在 Inspector 演示 end-to-end 流程。
- Day7: 调优、缓存、写 README、生成提交 ZIP（排除 .venv / logs）。

9) 风险与注意事项
- API Key 与 secrets：使用 `sops` 或环境变量管理，切勿硬编码在仓库。PPT 建议使用 `sops`。
- 成本控制：限制 LLM 调用频率、缓存热点 query 的结果、在 demo 使用小模型或本地 mock。 
- Windows 上某些包安装复杂，建议在 Linux 容器或 WSL 上开发生产化索引。

10) 下一步我可以帮你做
- 生成 `tools/model_adapters.py` 与 `tools/aggregator_tool.py`（embedding + FAISS demo），并把 prompts 写入 `prompts/`，随后运行并用 Inspector 演示一次。

----

结束。
