"""极简 .env 加载器（纯 stdlib，不引 python-dotenv）。

优先级：CLI flag > 已有 shell 环境变量 > .env 文件 > 默认。
因此 ``apply_env`` 默认只补「缺失」的键，绝不覆盖已存在的 shell 值。

解析规则（保持简单可预测）：
- 行首 ``#`` 视为注释，空行跳过；
- 行内 ``#`` 不当注释剥（值里可能真含井号）；
- 去掉键值两端的空白，去掉值两侧成对的成对引号（``"`` 或 ``'``）。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_PAIR_QUOTES = ('"', "'")


def parse_env_text(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in _PAIR_QUOTES:
            val = val[1:-1]
        if key:
            out[key] = val
    return out


def load_env_file(path: Path | str) -> Dict[str, str]:
    """读 .env 文件 -> dict。文件不存在返回 {}。"""
    p = Path(path)
    if not p.is_file():
        return {}
    return parse_env_text(p.read_text(encoding="utf-8"))


def apply_env(parsed: Dict[str, str], *, overwrite: bool = False) -> List[str]:
    """把 parsed 写进 os.environ。默认只补缺失键；返回实际写入的键名列表。"""
    set_keys: List[str] = []
    for k, v in parsed.items():
        if overwrite or k not in os.environ:
            os.environ[k] = v
            if not overwrite:
                set_keys.append(k)
    if overwrite:
        set_keys = list(parsed.keys())
    return set_keys


def load_and_apply(
    path: Path | str, *, overwrite: bool = False
) -> Tuple[List[str], Optional[Path]]:
    """读文件 -> 应用到 os.environ -> 返回 (写入的键名, 文件路径 or None)。

    文件不存在时返回 ([], None)。只打印键名、绝不打印值。
    """
    p = Path(path)
    parsed = load_env_file(p)
    if not parsed:
        return ([], None if not p.is_file() else p)
    keys = apply_env(parsed, overwrite=overwrite)
    return (keys, p)
