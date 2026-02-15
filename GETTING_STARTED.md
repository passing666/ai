# 快速获取与运行（给队友）

当前仓库位于本机（尚未推送远端）: `C:/Users/ASUS/Downloads/YA_MCPServer_Template/YA_MCPServer_Template`，当前分支：`dev`。

下面是两类命令，供你或队友拷贝执行：

1) 如果你已经有远端仓库（替换 `<remote-url>`）：

```bash
# 把远端添加为 origin（如果已存在请跳过）
git remote add origin <remote-url>

# 推送本地分支到远端（首次推送可使用 -u）
git push -u origin dev
git push -u origin main
```

2) 如果你是队友，要从远端克隆（示例）：

```bash
# HTTPS
git clone https://<your-git-host>/<your-org>/<repo>.git
cd YA_MCPServer_Template
git checkout dev

# 或者使用 SSH（配置了 SSH key）
git clone git@<your-git-host>:<your-org>/<repo>.git
cd YA_MCPServer_Template
git checkout dev
```

3) 本地直接运行（如果你拿到源代码后）：

```powershell
python -m pip install --user uv
python -m uv sync
python -m uv run server.py

# Inspector（可视化调试）
pipx install "mcp[cli]"   # 如果尚未安装 pipx 与 mcp
mcp dev server.py
```

补充：更详细的运行与环境说明请参见 `HANDOFF.md`（同仓库根）。
