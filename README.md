## YA_MCPServer_YourTeam

[一句话功能简介]

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :--: | :--: | :--: | :--: |
|      |      |      |      |
|      |      |      |      |
|      |      |      |      |

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|          |          |      |      |      |
|          |          |      |      |      |
|          |          |      |      |      |

### Resource 列表

| 资源名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|          |          |      |      |      |
|          |          |      |      |      |
|          |          |      |      |      |

### Prompts 列表

| 指令名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|          |          |      |      |      |
|          |          |      |      |      |
|          |          |      |      |      |

### 项目结构

- `core`: [XXXX]
- `tools`: [XXXX]
- `config.yaml`: [XXXX(添加 XX 额外配置)]
- [XXXX(其他新添加的文件与目录介绍)]

### 一键启动 & Inspector 使用（快速上手）

1. 进入项目目录并同步依赖（使用 `uv` 或 pip）：
```
cd YA_MCPServer_Template
uv sync            # 或使用 python -m pip install -e .
```

2. 启动 MCP Server（SSE 模式，默认监听 `127.0.0.1:12345`）：
```
uv run server.py    # 或 python -m uv run server.py
```

3. 启动 MCP Inspector：
```
mcp dev server.py
```
在 Inspector 页面中选择 `transport = sse`，地址填 `http://127.0.0.1:12345`，点击 Connect。

4. 在 Inspector 的 Tools 面板调用示例：
 - `get_server_config("server.name")`
 - `greeting_tool("Alice")`
 - `aggregate_search("示例查询")`
 - `agent_aggregate_and_greet(query="论文主题", name="Alice")`  # 示例 Agent：聚合查询并问候

5. 若需要命令行测试，可用 `curl` 或编写简单的 Python MCP 客户端连接 SSE 端点。

6. 在本地直接运行示例脚本与端到端测试：

```bash
# 运行示例 agent（不使用 Inspector）
PYTHONPATH=. python examples/run_agent.py

# 运行新增的简单端到端测试脚本（会导入并执行示例脚本，做最小断言）
PYTHONPATH=. python examples/end_to_end_test.py
```

### 其他需要说明的情况

- 在 `sops` 模块中添加的密钥变量分别用于什么功能
- 是否使用了 PyTorch、Tensorflow 等深度学习框架
- 是否使用了机器学习、深度学习模型
