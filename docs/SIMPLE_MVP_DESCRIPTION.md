**简化版（MVP）说明**

目的：在现有项目基础上提供一个最小可演示的聚合服务（/aggregate_search），支持本地资源 + 一个免费外部 provider（Wikipedia），并能通过 MCP Inspector 调试。

范围（Scope）：
- 最小接口：`POST /aggregate_search` 接受查询并并行调用 provider，返回标准化的文档列表（Doc schema）。
- 辅助接口：`GET /providers` 列出已启用的 provider；`POST /retrieve`（按 id 返回完整文档）。
- Provider：实现两类适配器：`local`（workspace 示例数据），`web_wiki`（调用 Wikipedia REST API 并将条目映射为 Doc）。
- 去重/合并：基于 `source_id` / 标题做简单去重（保留最高质量条目）。
- 不包含：向量索引（FAISS）、LLM reranker、并行大规模采集（可作为后续任务）。

Doc（规范化项）：每个返回条目包含字段：
- `id`：唯一标识（provider 名 + 原 id）。
- `title`：文档标题。
- `text`：正文或摘要（可截断到 2000 字符）。
- `score`：提供者原始相关性分数或启发式评分（0-1）。
- `provider`：provider 名称（`local` 或 `web_wiki`）。
- `source_url`：如果有则返回原始链接。
- `metadata`：可选字典（发布时间、作者等）。

示例请求：

POST /aggregate_search

{
  "q": "什么是卷积神经网络",
  "limit": 6
}

示例响应（简化）：

{
  "results": [
    {"id":"web_wiki:Convolutional_neural_network","title":"Convolutional neural network","text":"...摘要...","score":0.86,"provider":"web_wiki","source_url":"https://en.wikipedia.org/...","metadata":{}},
    {"id":"local:notes-001","title":"CNN 简明笔记","text":"...","score":0.72,"provider":"local","source_url":null,"metadata":{}}
  ]
}

实现要点（文件与位置建议）：
- `tools/aggregator_tool.py`：实现并发调用 providers、合并与去重逻辑、接口 handlers（MCP Tool 或 FastAPI route）。
- `providers/web_wiki.py`：实现 `search(q, limit)` 返回 Doc 列表；调用 Wikipedia 查询接口并规范化字段。
- `providers/local_provider.py`：读取 `resources/sample_data.json` 并做简单文本匹配返回结果（快速可控演示）。
- `prompts/`：保留提示词但 MVP 不依赖 LLM。

并发与超时：
- 每个 provider 并发请求，单个 provider 超时 3s；整体请求超时 6s（可配置）。

简单去重策略：
- 按 `title` 标准化（小写、去标点）做哈希；同一哈希只保留最高 `score` 条目。

开发与运行（快速上手）：

1) 在项目根运行（虚拟环境已激活）：

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e .
uvicorn server:app --reload
```

2) 使用 Inspector 调试（已安装 `mcp`）：

```powershell
mcp dev server.py
或
mcp dev tools/aggregator_tool.py
```

3) 测试 API（示例 curl）：

```powershell
curl -X POST http://localhost:8000/aggregate_search -H "Content-Type: application/json" -d "{\"q\":\"卷积神经网络\",\"limit\":4}"
```

配置 Deepseek API Key（详细步骤）：

为实现自然语言回答（RAG + LLM），需要把你的 Deepseek API Key 放入运行环境。下面按 Windows（PowerShell）与开发友好的 `.env` 两种常见方式说明。请勿将密钥写入代码或提交到公开仓库。

- 临时会话（仅当前 PowerShell 窗口，适合测试）：
  ```powershell
  $env:DEEPSEEK_API_KEY = "sk-..."
  uvicorn server:app --reload
  ```
  关闭该终端后变量失效。

- 永久用户环境变量（Windows 用户变量）：
  ```powershell
  setx DEEPSEEK_API_KEY "sk-..."
  ```
  运行后打开新终端生效；若密钥泄露，请在 Deepseek 控制台撤销并生成新密钥。

- 使用 `.env` 文件（推荐本地开发，需在 `.gitignore` 中忽略）：
  1. 在项目根创建 `.env`，内容：
     ```text
     DEEPSEEK_API_KEY=sk-...
     ```
  2. 在代码入口加载：
     ```python
     from dotenv import load_dotenv
     load_dotenv()
     import os
     key = os.getenv("DEEPSEEK_API_KEY")
     ```
  3. 安装依赖：`pip install python-dotenv`

- 验证脚本（快速检测环境变量）：
  在项目根创建 `scripts/check_key.py`：
  ```python
  import os
  if __name__ == '__main__':
      k = os.getenv('DEEPSEEK_API_KEY')
      print('DEEPSEEK_API_KEY set' if k else 'DEEPSEEK_API_KEY NOT set')
  ```
  运行：
  ```powershell
  python scripts/check_key.py
  ```

- CI/Actions：把密钥添加为仓库 Secret 名称 `DEEPSEEK_API_KEY`，在 workflow 中用 `secrets.DEEPSEEK_API_KEY` 引用。

安全与治理建议：
- 永不在聊天、Issue、PR、或公共仓库粘贴密钥；若误泄露，立即在 Deepseek 控制台撤销。 
- 为演示创建受限权限的 API Key（尽可能限制调用配额和可用功能）。

关于 Deepseek 集成说明（概要）：
- Deepseek 的具体 API 细节请参照 Deepseek 官方文档；典型工作流为：向 Deepseek 的检索或生成端点发送带 `DEEPSEEK_API_KEY` 的 HTTP 请求，解析返回的 JSON 并将结果映射为内部 `Doc` schema。示例：
  - 对应 `utils/deepseek_client.py` 的实现需要封装认证头、超时与错误处理；不要在代码中硬编码 endpoint 或 key。
  - 在 `tools/answer_tool.py` 中调用 `utils/deepseek_client.py` 的生成或检索方法以获取自然语言答案或作为 RAG 的后端 LLM。

结合老师的 PPT：老师的演示与 Inspector 调试步骤有相关说明（如运行与调试命令示例），参见课程资料 [人工智能引论智能体作业.pptx](人工智能引论智能体作业.pptx) 中关于启动与 Inspector 使用的幻灯片，可用于调试 RAG 调用链与查看 provider 请求/响应。

验收标准（最小演示）：
- `/aggregate_search` 返回本地与 Wikipedia 条目混合且格式化的 `results`。
- Inspector 能看到工具调用与 provider 请求细节（请求/响应、耗时）。
- README 中包含上述运行与测试步骤。


拆分建议（3 人，详尽职责与文件说明）

以下为 3 人分工建议，包含每个文件/模块的预期职责，便于并行开发与清晰交付。

- 人员 A — Backend (聚合与 API)：
  - 主要负责：实现聚合逻辑、/answer 路由、错误边界与单元测试。
  - 关键文件：
    - `tools/aggregator_tool.py`：
      - 功能：封装对已注册 providers 的并发查询（search），汇总结果，应用去重/合并策略，并返回标准化 Doc 列表。
      - 输出：`results` 列表，包含 `id,title,text,score,provider,source_url,metadata`。
    - `tools/answer_tool.py`：
      - 功能：实现 `/answer` 或 `answer()` 接口；调用 `aggregator_tool.search()`（或 POST /aggregate_search），选取 top-k 文档，构建 RAG prompt，调用 `utils/openai_client.py` 获取 LLM 回答，格式化并返回自然语言答案和引用来源。
      - 错误处理：当 LLM 或 provider 超时，应返回合理的降级消息（例如“部分来源不可用”）。
    - `server.py` 或项目的路由注册点：
      - 功能：为 `/aggregate_search` 和 `/answer` 注册 HTTP/MCP 路由或 Tool Handler（依项目现有风格），暴露给 Inspector。
    - `tests/test_aggregator.py`、`tests/test_answer.py`：
      - 功能：覆盖聚合与 RAG 拼接逻辑的单元/集成测试（可用 mock OpenAI 响应）。

- 人员 B — Providers（数据源适配器）：
  - 主要负责：实现 provider 适配器、实现 local 示例数据源与 Wikipedia provider，并保证返回统一 Doc schema。
  - 关键文件：
    - `providers/web_wiki.py`：
      - 功能：调用 Wikipedia API（或其他免费 API），实现 `search(q, limit)` 和可选 `get(id)`，把结果规范化为 Doc 列表（含摘要/链接/score）。
      - 注意：实现超时、重试（短次数）、并保证异常不会影响整体聚合流程。
    - `providers/local_provider.py`：
      - 功能：读取 `resources/sample_data.json`（或 `resources/*.md`），实现基于关键字的快速匹配搜索，返回 Doc 列表；用于离线演示与单元测试。
    - `providers/__init__.py`：
      - 功能：provider 注册与发现（比如通过配置文件启用 `local` 或 `web_wiki`）。
    - `resources/sample_data.json`：
      - 功能：包含若干条示例文档（id、title、text、metadata），便于本地演示与断言。

- 人员 C — 文档、Inspector 与运行体验：
  - 主要负责：使用说明、提示词模板、Inspector 调试脚本、演示脚本与最终验收文档。
  - 关键文件：
    - `docs/SIMPLE_MVP_DESCRIPTION.md`：
      - 功能：保持运行说明、API 规范、分工与验收标准的最新状态（你当前正在编辑的文件）。
    - `prompts/rag_prompt.txt`：
      - 功能：RAG 模板，用于把 top-k 文档拼接进 LLM prompt（包含回答要求与引用输出格式示例）。
    - `utils/openai_client.py`：
      - 功能：封装对 OpenAI 风格 API 的请求（读取 `OPENAI_API_KEY` 环境变量、设置超时、处理重试与错误；对返回做最小包装）。
    - `scripts/check_key.py`：
      - 功能：帮助用户快速验证环境变量 `OPENAI_API_KEY` 是否正确加载（便于课堂/演示前检查）。
    - `scripts/inspector_demo.sh` / `scripts/inspector_demo.ps1`：
      - 功能：一键启动 Inspector demo 步骤（启动 server、启动 mcp dev、执行示例请求并打印示例输出），并在文档中引用老师 PPT 中的调试步骤。
    - `examples/end_to_end_demo.py` 或 `examples/end_to_end.sh`：
      - 功能：演示完整流程：调用 `/aggregate_search` → `/answer`，并打印 LLM 返回与引用来源，便于课堂演示。

并行开发建议：
- 在实现初期用 `local` provider + sample data 完成端到端路径（Backend + Docs 并行），Providers 再补充 `web_wiki`。这样能保证早期可演示的闭环。
- 使用简单的接口契约（例如 `Provider.search(q, limit) -> List[Doc]`）以便并行开发时契合。

验收标准（与分工对应）：
- Backend：`/answer` 能在 6s 内返回合理答案（或明确超时降级）；日志中能看到 provider 调用耗时。
- Providers：`web_wiki` 在多数查询下返回至少 1 条可用 Doc，`local` provider 可覆盖 10 条示例查询。
- Docs/Inspector：`scripts/inspector_demo.*` 能演示一次完整调试流程，文档中包含 PPT 对应幻灯片编号或简要引用说明。

备注：每个文件应尽量保持小、单一职责，便于测试与替换（例如未来把 `openai_client` 替换为其他 LLM 客户端时影响最小）。


后续拓展（非必须）：
- 集成 embeddings + 向量检索、LLM reranker、更多 provider（arXiv、Crossref）、缓存与限流。

备注：此文档为“简化版（MVP）”说明，目标是短时内产出可演示闭环并通过 Inspector 调试。实现时应保留接口兼容性以便后续逐步升级。

演示示例：完整交互流程（示例问题→中间步骤→自然语言回答）

场景：用户询问“卷积神经网络（CNN）主要用于什么？”系统使用 `local` + `web_wiki` 聚合，然后用 Deepseek 生成最终自然语言答案并给出来源。

1) 用户请求（示例 HTTP）：

POST /answer
{
  "q": "卷积神经网络主要用于什么？",
  "limit": 4
}

2) 聚合调用（`tools/answer_tool.py` 内部行为，伪日志）：
- 调用：`aggregator_tool.search(q="卷积神经网络主要用于什么？", limit=4)`
- 并行调用 providers：
  - `local` 返回 1 条：{"id":"local:notes-001","title":"CNN 简明笔记","text":"CNN 常用于图像分类、目标检测和语义分割。...","score":0.72}
  - `web_wiki`（Wikipedia）返回 2 条：
    - {"id":"web_wiki:Convolutional_neural_network","title":"Convolutional neural network","text":"A convolutional neural network (CNN) is a class of deep neural networks commonly used to analyze visual imagery...","score":0.86,"source_url":"https://en.wikipedia.org/..."}
    - {"id":"web_wiki:Applications","title":"Applications of CNN","text":"CNNs are applied in image recognition, object detection, and more...","score":0.74}

3) 合并/去重（`aggregator_tool.py`）：
- 标准化标题并去重（保留 score 高的条目），输出 top-3 文档给 RAG 步骤。

4) 构建 RAG prompt（`prompts/rag_prompt.txt` 模板示例，片段）：
```
You are a helpful assistant. Use the provided documents to answer the user's question.
User question: "卷积神经网络主要用于什么？"

Documents:
[1] Title: Convolutional neural network
Text: A convolutional neural network (CNN) is a class of deep neural networks commonly used to analyze visual imagery...
[2] Title: CNN 简明笔记
Text: CNN 常用于图像分类、目标检测和语义分割。

Answer concisely in Chinese, and list 1-3 concise citations with source URLs if available.
```

5) 调用 Deepseek（`utils/deepseek_client.py`）：
- 请求：POST `https://api.deepseek.example/generate` 带 `Authorization: Bearer <DEEPSEEK_API_KEY>` 与上面的 prompt。
- 返回（示例）：{"answer":"卷积神经网络（CNN）主要用于处理视觉相关任务，如图像分类、目标检测和语义分割。此外也常用于视频分析和某些序列数据的特征提取。","sources":[{"id":"web_wiki:Convolutional_neural_network","url":"https://en.wikipedia.org/..."},{"id":"local:notes-001"}]}

6) 后处理与返回（`tools/answer_tool.py`）：
- 格式化最终响应为：

{
  "answer": "卷积神经网络（CNN）主要用于处理视觉相关任务，如图像分类、目标检测和语义分割。此外也常用于视频分析和某些序列数据的特征提取。",
  "citations": [
    {"id":"web_wiki:Convolutional_neural_network","url":"https://en.wikipedia.org/..."},
    {"id":"local:notes-001","url":null}
  ],
  "debug": {
    "providers_called": ["local","web_wiki"],
    "provider_times_ms": {"local":45,"web_wiki":220},
    "aggregate_time_ms": 280,
    "deepseek_time_ms": 420
  }
}

Inspector 视角（调试要点）：
- 在 Inspector 中可以看到：
  - `aggregator_tool` 的 provider 请求/响应（包含响应体和耗时），
  - RAG prompt 内容（可在 `tools/answer_tool.py` 的日志中输出），
  - Deepseek 请求/响应（在 `utils/deepseek_client.py` 可选择记录部分返回以便调试，但注意不要记录 API Key）。

说明：以上示例中的 URL 与时间为示例值；实际运行时 `provider_times_ms` 与 `deepseek_time_ms` 基于真实网络与模型响应。

