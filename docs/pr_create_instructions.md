# 如何在本地创建分支、提交与发起 PR

下面的步骤在你的开发机上执行（仓库根目录），会把刚才的修复提交到一个新分支并打开 GitHub PR。你可以按需调整分支名与远端名（`origin`）。

推荐命令（Git + gh CLI）：

```bash
# 切换到仓库根
cd "C:/Users/ASUS/Downloads/YA_MCPServer_Template/YA_MCPServer_Template"

# 创建并切换到新分支
git checkout -b fix/deepseek-chat-payload

# 添加修改并提交
git add utils/deepseek_client.py docs/development-guides/backend_api_contract.md docs/deepseek_issue_report.md
git commit -m "fix(deepseek): use chat-format payload and correct endpoint; update docs"

# 推送分支到远端
git push -u origin fix/deepseek-chat-payload

# 使用 GitHub CLI 打开 PR（会交互让你填写描述）
gh pr create --fill --title "fix: deepseek chat payload + endpoint" --body-file docs/pr_description.md
```

如果你没有 `gh`：在推送后，打开 GitHub 仓库页面，点击 Compare & pull request，然后填入 `docs/pr_description.md` 的内容作为 PR 描述。

注意：PR 不会包含本地的 `.env`（该文件已被 `.gitignore` 忽略），提交不会泄露密钥。
