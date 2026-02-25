## 掩码化请求/响应日志（已捕获）

1) 失败样例（错误请求体 / 旧 endpoint）：

```
TIME: 2026-02-24T06:39:03Z
REQUEST: POST https://api.deepseek.com/v1/chat/completions
HEADERS: {Authorization: Bearer sk-5***************************7027, Content-Type: application/json}
BODY: {"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}]}
RESPONSE STATUS: 401
RESPONSE BODY: Authentication Fails (governor)
TRACE ID: e0dab108d1e6658b8330f5c4e230408b
```

2) 成功样例（修复后）：

```
TIME: 2026-02-24T07:08:43Z
REQUEST: POST https://api.deepseek.com/v1/chat/completions
HEADERS: {Authorization: Bearer sk-5***************************7027, Content-Type: application/json}
BODY: {"model":"deepseek-chat","messages":[{"role":"user","content":"Hello from patched client test"}]}
RESPONSE STATUS: 200
RESPONSE BODY: {"object":"chat.completion","choices":[{"message":{"role":"assistant","content":"Hello! It looks like you're testing a patched client. How can I assist you today?"}}],...}
TRACE ID: 377c865e203eb3f4b2b7f82b6997f275
```

我可以把更完整的捕获（包含 HTTP header 字段与完整 body，均已掩码化）保存为 `docs/deepseek_masked_logs.md`，如果你同意我就创建该文件。 
# Deepseek 接入失败 — 错误报告（供发送给 Deepseek 支持）

> 生成日期：2026-02-23

## 概要

- 项目：YA_MCPServer_Template（本地 RAG + Deepseek 生成后端集成）
- 问题：在用用户提供的 API Key 与 endpoint 运行真实 E2E 时，Deepseek 请求收到 `401 Unauthorized`；在早期尝试中曾出现短暂的 DNS/addrinfo 解析错误。网络可达性与 TCP 连接已验证。

## 环境信息

- 操作系统：Windows（用户开发机）
- Python：3.14（异步 async/await）
- HTTP 客户端：`httpx`（异步）
- Deepseek endpoint（用户写入到 `.env`）：https://api.deepseek.com/v1/chat/completions
- 已用 API Key（已做掩码）：sk-5***************************7027

（.env 文件被加入 `.gitignore`，因此秘钥未被提交到版本库）

## 复现步骤（已在用户环境执行）

1. 在项目根目录运行本地 E2E inspector：`tools.e2e_inspector.run(..., mode='real')`。
2. 系统通过 `tools.answer_tool` 组装 RAG prompt 并调用 `utils.deepseek_client.generate(prompt)`。
3. `deepseek_client.generate` 使用 `Authorization: Bearer <DEEPSEEK_API_KEY>` 发起 POST 到 `DEEPSEEK_ENDPOINT`，并有重试/退避逻辑（多次重试后返回错误）。

## 已执行的本地诊断与关键输出（已掩码敏感信息）

- DNS 解析（socket / nslookup）：解析到 IP 列表，例如 `116.205.40.113, 116.205.40.114`，并经由 huaweicloud CDN/WAF。
- 原始 TCP 连接（socket.connect）到 `api.deepseek.com:443`：成功（`TcpTestSucceeded = True`）。
- `httpx` 对目标 endpoint 做 `HEAD` 请求：返回 `HTTP 401 Unauthorized`（表明服务器可达但认证/权限或请求格式有问题）。
- 早期尝试的异常（暂时性）：`[Errno 11001] getaddrinfo failed`（疑为初次解析或网络抖动造成，后续诊断显示 DNS/TCP 可达）。
- `tracert` 在网络路径上出现超时（常见于 CDN/WAF 节点对 ICMP 的过滤）。
- 未发现 WinHTTP 或环境代理变量（`HTTP_PROXY`, `HTTPS_PROXY` 为空）。

截取的请求头/响应片段（敏感项已掩码）：

```
REQUEST HEADERS:
- Authorization: Bearer sk-5***************************7027
- Content-Type: application/json
- User-Agent: python-httpx/...

RESPONSE:
- HTTP/1.1 401 Unauthorized
- Server: huaweicloud-cdn/...
```

完整的请求/响应 body 和多次尝试的堆栈日志可以在本地捕获的 inspector 输出中提供（如需我可附上完整掩码日志）。

## 我们已尝试的缓解/确认项

- 将 `DEEPSEEK_ENDPOINT` 明确写入 `.env`（此前仅写入 API Key，导致部分尝试使用默认或空 endpoint 并出现 getaddrinfo 错误）。
- 本地直接用 `httpx` 对 endpoint 发起 `HEAD` 请求以做快速探测（结果为 401，而非网络不可达）。
- 检查并确认无本地代理设置或 WinHTTP 代理阻断。

## 可能的根因猜测

1. 认证/权限问题：API Key 无效、过期、未开通相应 scope、或被限制（IP 白名单 / 时间 / 用量等）。
2. 请求格式不匹配：服务端期待不同的字段名、认证方式（例如不同的 header 名），或需要额外的 header（如 `X-...`）或 body 结构（`messages` vs `prompt`）。
3. WAF/CDN 策略：CDN（huaweicloud）在接入层拦截或限流，导致需要特定的 SNI、User-Agent 或白名单设置。
4. 早期的 `getaddrinfo` 报错：可能由临时 DNS 问题或环境初始化顺序导致，但当前已可解析。

## 请 Deepseek 支持确认的清单（可直接复制发送）

1. 我们使用 `Authorization: Bearer <key>`（示例：`Authorization: Bearer sk-5***************************7027`）发起 POST 到 `https://api.deepseek.com/v1/chat/completions`，请确认该 key 在服务端是有效且允许此 endpoint 的调用。
2. 如果有权限/Scope 或 IP 白名单限制，请告知如何查看或解除（或确认是否该 key 已被禁用）。
3. 服务端期望的请求 body schema 示例（最小可成功的示例请求体），以及是否需要 `messages`、`prompt` 或其他字段。
4. 是否需要额外/特定的 headers（例如 `X-...`、`Accept`、自定义 `User-Agent`）或 JSON 中的特定字段以绕开 CDN/WAF 误报。
5. 如果接入层使用了 CDN/WAF（我们观察到来自 huaweicloud 的 CDN/防火墙），能否在你方查阅到因 WAF 规则触发的拦截记录（基于上述时间戳）并反馈给我们。
6. 如果需要，我们可以提供完整（但掩码化）的请求/响应对和时间戳以供你方排查。

## 建议的下一步（对我们 / 对 Deepseek）

- 你方确认认证与请求格式后，我方会按需调整 `utils/deepseek_client.py` 中的 header 或 body 格式并再跑一次 E2E，或由你方在服务端放行该 key 以便我们继续测试。
- 如果是 WAF 拦截，请协助查看拦截日志或建议需携带的 header/SNI/User-Agent。

## 附件与可提供的额外信息

- 我可以提供以下项目供支持团队参考：
  - 掩码后的完整请求/响应日志（包含时间戳与重试次数）。
  - 本地诊断脚本输出（socket/nslookup/Test-NetConnection/httpx HEAD/tracert）。
  - 项目中用于调用的简版代码片段（`utils/deepseek_client.generate` 的实现），便于你方重现。

---

<!-- CI trigger: harmless edit to re-run GitHub Actions and verify async test deps -->
