"""GAIA 风格答案打分：归一化 + 精确/子串匹配。

NOTE: 官方 GAIA scorer 未拉到（HF gated + 本机网络封），本版为合理近似；
接真数据时按官方脚本对齐（spec §10）。
"""
from __future__ import annotations

import re
import unicodedata

_ARTICLES = {"a", "an", "the"}


def normalize(answer: str) -> str:
    """归一化：NFKC、小写、去千分位逗号、去整数值的 .0、去标点、去前导冠词、压空白。"""
    if not answer:
        return ""
    s = unicodedata.normalize("NFKC", str(answer))
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower().strip()
    # 千分位：1,000 -> 1000（逗号夹在数字间、后跟 3 位 + 非数字/结尾）
    s = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", s)
    # 整数值小数：1.0 -> 1（.0+ 后接非数字或结尾）
    s = re.sub(r"(\d)\.0+(?=\D|$)", r"\1", s)
    # 去标点：保留 \w 与 "."（小数点），其余转空格
    s = re.sub(r"[^\w.]+", " ", s, flags=re.UNICODE)
    tokens = [t.strip(".") for t in s.split() if t.strip(".")]
    while tokens and tokens[0] in _ARTICLES:
        tokens = tokens[1:]
    return " ".join(tokens)


def score(prediction: str, gold: str) -> bool:
    """归一后预测 == 金标即对；否则按金标 token 数判定：

    - 单 token 金标（单词/单数，如 "17"/"paris"）：必须整 token 命中预测
      （避免 "17" 子串误匹配 "17000"）。
    - 多 token 金标（短语，如 "the castle"）：金标为预测子串即对
      （"the castle" in "int the castle day"）。
    """
    np = normalize(prediction)
    ng = normalize(gold)
    if not ng:
        return not np
    if np == ng:
        return True
    ng_tokens = ng.split()
    if len(ng_tokens) == 1:
        return ng in np.split()
    return ng in np
