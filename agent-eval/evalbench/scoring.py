"""纯计算逻辑：从评估器的连续分数到二分类准确率。

不含 LLM、不含 IO，可单独单测。语义：

- ``SampleResult.predicted`` —— 评估器分数 >= ``threshold`` 判为「相关」(1)，
  否则「不相关」(0)；errored (score is None) 时为 ``None``。
- ``SampleResult.correct`` —— 预测与金标 label 相同为 True；errored 永远 False。
- ``Metrics.accuracy`` —— ``n_correct / n_total``，errored 计为错（保守门控）。
- 混淆矩阵只覆盖「判过」的样本 (score is not None)，因此 ``confusion.accuracy``
  在有 error 时会高于 headline ``accuracy`` —— 报告里两个都报，透明。
- 门控 ``passes_gate`` 默认 0.80：准确率达到门限即视为可发布。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

DEFAULT_GATE = 0.80


@dataclass
class SampleResult:
    """单条样本的评估结果。"""

    id: str
    input: str
    output: str
    label: int  # 1 = 相关，0 = 不相关
    sample_type: str  # positive | strong_negative | hard_negative
    score: Optional[float]  # 评估器分数 0..1；errored 时为 None
    threshold: float = 0.5
    reason: Optional[str] = None
    error: Optional[str] = None

    @property
    def judged(self) -> bool:
        return self.score is not None

    @property
    def predicted(self) -> Optional[int]:
        if not self.judged:
            return None
        return 1 if self.score >= self.threshold else 0

    @property
    def correct(self) -> bool:
        p = self.predicted
        return p is not None and p == self.label


@dataclass
class ConfusionMatrix:
    """二分类混淆矩阵（正类 = 「相关」）。只覆盖判过的样本。"""

    tp: int = 0  # label1 pred1
    fp: int = 0  # label0 pred1
    fn: int = 0  # label1 pred0
    tn: int = 0  # label0 pred0

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def accuracy(self) -> float:
        t = self.total
        return (self.tp + self.tn) / t if t else 0.0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


@dataclass
class TypeBreakdown:
    sample_type: str
    total: int
    correct: int
    errored: int

    @property
    def judged(self) -> int:
        return self.total - self.errored

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


@dataclass
class Metrics:
    """整个数据集的汇总指标。"""

    results: List[SampleResult]

    @property
    def n_total(self) -> int:
        return len(self.results)

    @property
    def n_judged(self) -> int:
        return sum(1 for r in self.results if r.judged)

    @property
    def n_errored(self) -> int:
        return self.n_total - self.n_judged

    @property
    def n_correct(self) -> int:
        return sum(1 for r in self.results if r.correct)

    @property
    def accuracy(self) -> float:
        """headline：correct / total，errored 计为错。"""
        return self.n_correct / self.n_total if self.n_total else 0.0

    @property
    def accuracy_among_judged(self) -> float:
        return self.n_correct / self.n_judged if self.n_judged else 0.0

    @property
    def coverage(self) -> float:
        return self.n_judged / self.n_total if self.n_total else 0.0

    # —— P/R/F1 委托到 confusion，方便直接 m.precision ——
    @property
    def precision(self) -> float:
        return self.confusion.precision

    @property
    def recall(self) -> float:
        return self.confusion.recall

    @property
    def f1(self) -> float:
        return self.confusion.f1

    @property
    def confusion(self) -> ConfusionMatrix:
        cm = ConfusionMatrix()
        for r in self.results:
            p = r.predicted
            if p is None:
                continue  # errored 不入混淆矩阵
            if r.label == 1 and p == 1:
                cm.tp += 1
            elif r.label == 0 and p == 1:
                cm.fp += 1
            elif r.label == 1 and p == 0:
                cm.fn += 1
            else:
                cm.tn += 1
        return cm

    @property
    def by_type(self) -> Dict[str, TypeBreakdown]:
        agg: Dict[str, TypeBreakdown] = {}
        for r in self.results:
            b = agg.setdefault(
                r.sample_type, TypeBreakdown(r.sample_type, 0, 0, 0)
            )
            b.total += 1
            if r.correct:
                b.correct += 1
            if not r.judged:
                b.errored += 1
        return agg

    def passes_gate(self, gate: float = DEFAULT_GATE) -> bool:
        return self.accuracy >= gate
