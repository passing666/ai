# PR: fix(deepseek): use chat-format payload and correct endpoint

## 概要

修复 `utils/deepseek_client.py` 中向 Deepseek 发送请求的格式与默认 endpoint：

- 将默认 endpoint 修正为 `https://api.deepseek.com/v1/chat/completions`。
- 将请求体由 `{"prompt": "..."}` 改为 chat 格式：`{"model":"deepseek-chat","messages":[{"role":"user","content": prompt}]}`。
- 更新相应文档：`docs/development-guides/backend_api_contract.md`，并补充了示例与注意事项。

## 变更文件

- `utils/deepseek_client.py` — 修复默认 endpoint 与 payload 格式。
- `docs/development-guides/backend_api_contract.md` — 添加 Deepseek 调用示例与修复说明。
- `docs/deepseek_issue_report.md` — 追加掩码化的测试请求/响应日志（含 trace id）。

## 验证步骤

1. 在开发机激活虚拟环境并加载 `.env` 中的 `DEEPSEEK_API_KEY`。
2. 运行以下脚本或命令（示例）：

```bash
python - <<'PY'
import asyncio
from modules.YA_Secrets import load_dotenv, get_secret
import httpx

load_dotenv()
key = get_secret('DEEPSEEK_API_KEY')
payload = {"model":"deepseek-chat","messages":[{"role":"user","content":"Hello from patched client test"}]}
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
r = httpx.post('https://api.deepseek.com/v1/chat/completions', json=payload, headers=headers, timeout=15.0)
print(r.status_code, r.text)
PY
```

预期结果：返回 `200` 并包含 `chat.completion` 的 JSON 响应。

## 备注与后续工作

- 请在合并后在 CI 中加入自动化测试（下游任务：添加 GitHub Actions，运行 pytest 与格式检查）。
- 我已在 `docs/pr_create_instructions.md` 中写出本地创建分支和打开 PR 的命令，便于你快速执行。
