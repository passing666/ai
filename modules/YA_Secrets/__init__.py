"""YA_Secrets

轻量的辅助模块，用于统一从环境或项目根目录的 `.env` 中读取敏感配置（API 密钥等），
并提供可选的将密钥写入 `.env` 的 helper。请在写入真实密钥前确认这是你想要的行为。

设计准则：
- 读取优先使用运行时环境变量（`os.environ`）。
- 提供 `load_dotenv` 来从项目根的 `.env` 文件加载到环境中（不依赖第三方库）。
- `set_secret(..., persist=True)` 可将键写入或更新到 `.env`（仅在用户显式调用时执行）。
"""

from __future__ import annotations

import os
from typing import Optional

_ENV_FILE = os.path.join(os.getcwd(), ".env")


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """从环境中读取密钥，若不存在则返回 `default`。

    优先级：`os.environ` -> `default`。
    """
    return os.environ.get(name, default)


def load_dotenv(path: Optional[str] = None) -> None:
    """从指定的 `.env` 文件解析键值并注入 `os.environ`（不会覆盖已存在的环境变量）。

    文件格式：每行 `KEY=VALUE`，支持以 `#` 开头的注释和空行。
    """
    p = path or _ENV_FILE
    try:
        with open(p, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"')
                if k and k not in os.environ:
                    os.environ[k] = v
    except FileNotFoundError:
        return


def set_secret(
    name: str, value: str, persist: bool = False, path: Optional[str] = None
) -> None:
    """在运行时将密钥写入 `os.environ`，并可选地持久化到 `.env`。

    persist=True 时会在指定 `path`（或项目根 `.env`）中新增或更新对应项。
    注意：将密钥写入仓库文件有泄露风险，请仅在你确信安全的环境下使用。
    """
    os.environ[name] = value
    if not persist:
        return
    p = path or _ENV_FILE
    lines = []
    updated = False
    try:
        with open(p, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if not line or line.strip().startswith("#") or "=" not in line:
                    lines.append(line)
                    continue
                k, _ = line.split("=", 1)
                if k.strip() == name:
                    lines.append(f"{name}={value}")
                    updated = True
                else:
                    lines.append(line)
    except FileNotFoundError:
        # will create new file
        pass

    if not updated:
        lines.append(f"{name}={value}")

    # write atomically
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for L in lines:
            f.write(L + "\n")
    os.replace(tmp, p)
