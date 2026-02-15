# 项目交接与快速上手

本文档用于让队友通过 Git 获取本框架并快速运行示例（Windows 环境下说明）。若使用 Linux/Mac，请将 PowerShell 特定命令替换为对应 shell 命令。

## 克隆仓库（队友操作）

1. 使用 HTTPS 克隆：

```bash
git clone https://<your-git-host>/<your-org>/<repo>.git
cd YA_MCPServer_Template
git checkout dev   # 或 main，根据团队约定
```

2. 使用 SSH 克隆（已配置 SSH key）：

```bash
git clone git@<your-git-host>:<your-org>/<repo>.git
cd YA_MCPServer_Template
git checkout dev
```

（提示）如果你需要我把本地仓库推到远端，请提供远端仓库 URL，我可以帮你添加 remote 并示范 `git push` 命令。

## 本地环境快速准备

推荐使用 `uv` 来同步依赖并运行（老师推荐）。示例命令：

```powershell
# 安装 uv（若未安装）
python -m pip install --user uv

# 同步项目依赖（会执行 setup.py / pyproject 中的依赖）
python -m uv sync

# 启动 MCP Server（SSE 模式）
python -m uv run server.py
```

说明：若你更喜欢使用 venv，请在克隆后创建并激活虚拟环境并运行 `pip install -e .`。

## Inspector 与 MCP CLI（可视化调试）

1. 安装 `pipx` 并用它安装 `mcp` CLI（避免污染本地环境）：

```bash
python -m pip install --user pipx
python -m pipx ensurepath
pipx install "mcp[cli]"
```

2. 运行 Inspector：

```bash
mcp dev server.py
```

Inspector 会在本机启动代理并给出访问 URL（浏览器打开 URL 并填入 token 即可连接）。若 `mcp dev` 在尝试自动安装前端时失败，请先全局安装 Inspector 包：

```bash
npm install -g @modelcontextprotocol/inspector@0.20.0
```

3. 如果 `mcp` 在运行时报缺少模块（如 `pyyaml`），请在 pipx 管理的 `mcp` venv 中安装缺失依赖：

```bash
# 使用 pipx 向 mcp venv 安装依赖
python -m pipx runpip mcp install pyyaml colorlog art
```

## 运行示例与测试

- 运行示例 agent（不使用 Inspector）：

```bash
PYTHONPATH=. python examples/run_agent.py
```

- 运行快速端到端测试：

```bash
PYTHONPATH=. python examples/end_to_end_test.py
```

如果因为环境差异出现 `No module named 'mcp'` 的错误，可使用 pipx 管理的 `mcp` venv 下的 Python 来运行测试（路径因系统与用户而异，下面为示例占位，请替换为你本机的 pipx venv Python 路径）：

```powershell
# 示例（请替换 <PIPX_MCP_PYTHON_PATH> 为你本机 pipx mcp venv 中的 Python 可执行文件路径）
& '<PIPX_MCP_PYTHON_PATH>' examples/end_to_end_test.py
```

## Windows PowerShell 注意事项

- 如果 PowerShell 阻止执行脚本，临时放宽执行策略（仅对当前会话）：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

## 推送到远端（可选，需你提供 URL）

示例（首次推送 dev 分支）：

```bash
git remote add origin https://<your-git-host>/<your-org>/<repo>.git
git push -u origin dev
git push -u origin main
```

## 常见问题与注意点

- `pipx` 安装的 `mcp` 运行时与项目环境分离，若 import 出错请在 `mcp` venv 中安装缺失库（见上文）。
- Inspector 在首次自动安装前端时可能需要 `npm` 与网络访问权限，预先全局安装可以避免交互提示。
- 若团队希望使用 Docker 或 CI，我可以帮你添加 `Dockerfile` 与 `github-actions` 工作流模板。

## 我可以继续做的项（选填）

- 我可以把本地仓库推到你指定的远端并创建 release。
- 我可以添加 `Dockerfile` 与 `docker-compose` 示例。
- 我可以把端到端测试迁移为 `pytest` 并添加 GitHub Actions CI。

---

文件位置： [YA_MCPServer_Template/YA_MCPServer_Template/HANDOFF.md](YA_MCPServer_Template/YA_MCPServer_Template/HANDOFF.md)