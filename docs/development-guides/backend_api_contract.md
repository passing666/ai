# Backend `/answer` API — 数据契约
## Deepseek 调用样例与已知问题修复
下面给出可直接在终端运行的请求示例（请替换为你自己的完整 API Key 或使用会话环境变量）。
- Bash / curl:
```bash
curl https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-你的完整密钥" \
  -d '{
  "model": "deepseek-chat",
  "messages": [
  {"role": "user", "content": "Hello"}
  ]
  }'
```
- PowerShell (推荐在 Windows 上运行示例):
```powershell
$body = @{
  model = "deepseek-chat"
  messages = @(
  @{ role = "user"; content = "Hello" }
  )
} | ConvertTo-Json

$headers = @{
  "Content-Type" = "application/json"
  "Authorization" = "Bearer sk-你的完整密钥"
}

Invoke-RestMethod -Uri "https://api.deepseek.com/v1/chat/completions" \
  -Method Post \
  -Headers $headers \
  -Body $body
```
- Python (`httpx`):
```python
import httpx

headers = {"Authorization": "Bearer sk-你的完整密钥", "Content-Type": "application/json"}
payload = {"model":"deepseek-chat", "messages":[{"role":"user","content":"Hello"}]}

r = httpx.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=15.0)
print(r.status_code, r.text)
```
### 我们遇到的问题及解决方法（仓库变更说明）

- 问题描述：在最初实现中，项目的 `utils/deepseek_client.py` 使用了错误的默认 endpoint（`https://api.deepseek.example/v1/generate`）并以 `{"prompt": "..."}` 的格式发送请求，导致对方返回 `401` 或格式不匹配错误。
- 修复内容：已将默认 endpoint 改为 `https://api.deepseek.com/v1/chat/completions`，并把请求体改为 chat 格式：`{"model":"deepseek-chat","messages":[{"role":"user","content": prompt}]}`。
- 相关文件：`utils/deepseek_client.py`（已修改）。

### 验证结果（本地测试）

- 我们在开发环境使用仓库中写入的密钥直接发起请求（使用 `modules.YA_Secrets` 读取 `.env` 中的密钥），修复后请求返回 `200`，示例响应如下（已掩码化）：

```
STATUS: 200
BODY: {"id":..., "object":"chat.completion", "choices":[{"message":{"role":"assistant","content":"Hello! It looks like you're testing a patched client..."}}], ...}
```
- 之前的失败响应示例（由错误请求体/endpoint 触发）：

```
STATUS: 401
BODY: Authentication Fails (governor)
```

### 建议的接入注意事项

- 确保 `Authorization` header 精确为 `Bearer <完整密钥>`（Bearer 后有一个空格）。
- 请求 body 必须为合法 JSON，字段名与示例一致（`model`、`messages`）。
- 在本地使用 `.env` 管理密钥时，保证读取后无多余换行或空格（可用 `print(repr(api_key))` 验证）。
- 在生产中请勿在日志中打印完整密钥；在 debug 输出中仅显示掩码版本。

---
# Backend `/answer` API — 数据契约

目的：定义后端 `/answer` 路由（或本地 adapter）请求与响应结构，便于多组员并行实现并保证集成时兼容。

注意：本项目当前不修改 `server.py`；此契约用于前端、其他 provider 实现或本地 adapter 的对齐。

请求（POST /answer）示例 JSON:

{
  "question": "用户的自然语言问题字符串",
  "limit": 4,                     # 可选，默认 4
  "mode": "real",               # 可选："real" 或 "stub"，演示/测试用
  "debug": true                   # 可选，是否在响应中包含 debug 字段
}

响应示例 (成功):

{
  "answer": "生成的简洁回答字符串",
  "sources": [
    {"id": "doc-id-1", "title": "文档标题", "url": "http://..."}
  ],
  "debug": {
    "providers_called": ["local_provider", "web_provider"],
    "provider_times_ms": {"local_provider": 12.0, "web_provider": 150.2},
    "deepseek_time_ms": 320.5,
    "prompt": "<用于生成的 prompt 字符串（可选、在 debug=true 时返回）>",
    "deepseek_error": null
  }
}

降级/错误响应示例（当 Deepseek 或外部服务失败）：

{
  "answer": "无法从提供的文档中得出结论。",
  "sources": [],
  "debug": {
    "providers_called": ["local_provider"],
    "provider_times_ms": {"local_provider": 12.0},
    "deepseek_time_ms": null,
    "deepseek_error": "ConnectError: getaddrinfo failed"
  }
}

字段说明（关键项）:
- `answer` (string): 最终返回给用户的自然语言回答。
- `sources` (array): 引用的文档信息，元素至少包含 `id` 和 `title`，可选 `url`。
- `debug.providers_called` (array): 在此次请求中调用过的 provider 名称。
- `debug.provider_times_ms` (map): 每个 provider 的耗时（毫秒），用于构建性能指标。
- `debug.deepseek_time_ms` (number|null): Deepseek 请求耗时（毫秒），如果未调用则为 null。
- `debug.prompt` (string): 发送给生成模型的 prompt（仅在 debug=true 时返回以节约带宽）。
- `debug.deepseek_error` (string|null): Deepseek/生成层面的错误信息（如果有）。

注意事项：
- 在对外演示时（Inspector），建议将 `debug` 设为 true 以展示 prompt、provider_times 等信息。
- 生产环境应对 `debug.prompt` 与 `deepseek_error` 做脱敏/审查，避免泄露敏感信息。
