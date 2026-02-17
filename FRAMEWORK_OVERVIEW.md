# 框架使用与文件说明（仅含功能、文件说明与使用指南）

下面的内容只包含：框架主要功能、每个文件/文件夹的作用，以及队友如何克隆并在本地使用与扩展框架（不包含项目简介、开发/提交流程或团队信息）。

## 一：框架主要功能（简要）
- 以 MCP 协议暴露可被 LLM 调用的能力：Tools、Resources、Prompts。
- 支持两种运行方式：SSE（HTTP）和 stdio（标准输入/输出），便于本地调试与 Inspector 使用。
- 提供自动注册机制：放入 `tools/`、`resources/`、`prompts/` 下并使用相应装饰器即可被服务器发现并注册。
- 包含示例工具、示例资源、Agent 调度示例与最小端到端测试，便于快速上手与二次开发。

## 二：文件与文件夹说明（按分支组织）

下面按 `main` 与 `dev` 两个分支分别列出该分支上主要文件/目录的作用，便于队友知道应从哪个分支與入口開始開發或提交。

### main（稳定分支 — 用于评审/提交/打包）
- `server.py`：稳定的启动入口；负责读取 `config.yaml` 并启动 MCP Server（通常运行 SSE）。
- `config.yaml`：生产/评审默认配置（transport、host、port、server.name 等）。
- `pyproject.toml` / `setup.py`：定义项目安装与基础依赖，供评审机或同学一键安装。
- `tools/`（基础子集）：包含基础示例工具，如 `hello_tool.py`，用于展示最小能力集与评审验证。
- `resources/`（基础子集）：包含 `hello_resource.py` 等示例资源，供评审时读取项目说明或日志。
- `prompts/`（基础子集）：包含最基础的 Prompt 模板，便于评审环境直接调用。
- `README.md`：面向评审/使用者的快速上手文档（精简版）。

### dev（开发分支 — 用于集成与开发最新功能）
- `tools/aggregator_tool.py`：聚合 API 的实现（示例/占位），实现对多 provider 的统一封装、去重、排序與限流/缓存策略。
- `tools/agent_tool.py`：示例 Agent，演示如何组合多个工具进行复杂任务。
- `tools/test_calls.py`：本地调用脚本，用于快速调试单个 tool。
- `tools/providers/`（建议位置，若不存在可创建）：存放多源 provider 的实现（对接外部 API、内部 DB 等）。
- `examples/`：包含 `run_agent.py`、`end_to_end_test.py` 等示例脚本，供开发者做本地验证（这些通常不在 `main` 的精简提交中出现）。
- `FRAMEWORK_OVERVIEW.md`, `HANDOFF.md`, `GETTING_STARTED.md`：最新的开发/交接文档（位于 `dev`，合并到 `main` 前可校对）。

## 三：聚合 API（详细封装说明）
聚合 API 负责将多源检索封装成统一 Tool，供 Agent 以简单接口调用。

接口约定（公开函数）：
- `aggregate_search(query: str, max_results: int = 10, sources: Optional[List[str]] = None) -> dict`
  - 返回示例：
    ```json
    {"query": "...", "results": [{"source":"web","id":"...","title":"...","snippet":"...","url":"..."}, ...]}
    ```

核心实现要点：
- Provider 插件化：每个 provider 提供 `fetch(query, max_results)` 与 `normalize(raw)` 方法。
- 并发与超时：对多个 provider 并发调用（线程/async），设定超时与限流阈值。
- 错误隔离：单个 provider 出错不会导致整体失败，记录错误并继续返回其他 provider 结果。
- 去重策略：基于 URL 或标题哈希做简单去重；可按时间或相关度排序。
- 缓存层：内存缓存（TTL）或可插 Redis，减少重复调用。

示例 Provider 约定：
```python
class ExampleProvider:
    name = "example"
    def fetch(self, query, max_results):
        # 调用外部 API，返回 raw items
        return raw_items
    def normalize(self, raw_item):
        return {"id": raw_item["id"], "title": raw_item["title"], "snippet": raw_item.get("snippet",""), "url": raw_item.get("url",""), "source": self.name}
```

聚合器伪代码：
```python
def aggregate_search(query, max_results=10, sources=None):
    providers = load_providers(sources)
    futures = [executor.submit(p.fetch, query, max_results) for p in providers]
    collected = []
    for p, fut in zip(providers, futures):
        try:
            raw = fut.result(timeout=provider_timeout)
            collected.extend([p.normalize(r) for r in raw])
        except Exception:
            log.warning("provider %s failed", p.name)
    results = dedupe_and_score(collected)
    return {"query": query, "results": results[:max_results]}
```

扩展步骤（示例）：
1. 在 `tools/providers/` 新增 `my_provider.py`，实现 `fetch` 与 `normalize`。
2. 在 `tools/aggregator_tool.py` 注册该 provider 或添加动态发现逻辑。
3. 在 `examples/` 添加验证脚本并本地运行。

测试建议：为每个 provider 编写单元测试（模拟 API 返回），并为 `aggregate_search` 编写集成测试以验证去重、排序与错误隔离行为。

## 四：队友快速参考（从克隆到扩展）
1. 克隆并切 `dev`：
```bash
git clone https://github.com/passing666/ai.git
cd ai
git checkout dev
```
2. 同步依赖并激活环境（推荐 `uv`）：
```powershell
python -m pip install --user uv
python -m uv sync
# Windows activate: .venv\\Scripts\\activate
```
3. 启动服务器并在 Inspector 调试：
```powershell
python -m uv run server.py
pipx install "mcp[cli]"
mcp dev server.py
```
4. 本地直接验证新 Tool/Provider：
```bash
PYTHONPATH=. python examples/run_agent.py
```

---

已把聚合 API 的实现说明与按分支的文件说明合并入本文档。若需要，我接下来会把该修改 commit 并推送到 `dev`（現在准备执行）。

