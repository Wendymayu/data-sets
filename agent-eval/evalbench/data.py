"""加载评测基准数据集（通用 schema）。

JSON 顶层是带元信息的 dict，``samples`` 是样本列表，每条字段：
id / input / output / label(1=评估器要检测的属性 0=否) / sample_type / construction / source_dataset
不同评估器（相关性/敏感信息/准确性/AI味…）共用同一 schema，只是 label 语义随评估器变。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_FIELDS = ("id", "input", "output", "label", "sample_type")

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "benchmarks"
    / "relevance"
    / "agent_relevance_evaluator_benchmark.json"
)


def load_dataset(path: Path | str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    """读整个基准文件（含 name/purpose/statistics/samples 等元信息）。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_samples(path: Path | str = DEFAULT_DATA_PATH) -> List[Dict[str, Any]]:
    """只取 ``samples`` 列表，并校验每条必填字段。"""
    data = load_dataset(path)
    samples = data.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError(f"数据集 {path} 里没有非空 samples 列表")
    for i, s in enumerate(samples):
        missing = [k for k in REQUIRED_FIELDS if k not in s]
        if missing:
            raise ValueError(f"第 {i} 条样本缺字段 {missing}")
    return samples
