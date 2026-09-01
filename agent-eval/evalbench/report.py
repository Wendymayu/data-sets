"""把 Metrics 渲染成中文 markdown 报告 + 可序列化 JSON payload。

报告分块：标题/判定 -> 配置 -> 核心指标 -> 混淆矩阵 -> 按类型分布
-> 逐样本明细（错误优先）-> 错误样本。逐样本明细里 reason 截断到 60 字。

标题与混淆矩阵「正类」名按评估器档案参数化（``evaluator_label`` /
``positive_class`` / ``negative_class``），不再硬编码「相关性」。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from evalbench.scoring import Metrics, SampleResult

EVALUATOR_NAME = "AnswerRelevanceMetric"
REASON_TRUNC = 60


@dataclass
class ReportConfig:
    model_name: str
    threshold: float
    gate: float
    dataset_name: str
    timestamp: str
    evaluator_name: str = EVALUATOR_NAME  # 技术名（metric 类）
    evaluator_label: str = "相关性评估器"  # 报告标题用的人话名
    positive_class: str = "相关"  # label 1 含义，混淆矩阵「正类」
    negative_class: str = "不相关"  # label 0 含义


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _fmt_score(s: float | None) -> str:
    return "—" if s is None else f"{s:.2f}"


def _fmt_pred(p: int | None, cfg: ReportConfig) -> str:
    if p is None:
        return "errored"
    return cfg.positive_class if p == 1 else cfg.negative_class


def _verdict(m: Metrics, cfg: ReportConfig) -> str:
    if m.passes_gate(cfg.gate):
        return f"✅ 通过（准确率 {_pct(m.accuracy)} ≥ {_pct(cfg.gate)} 门限）"
    return f"❌ 未通过（准确率 {_pct(m.accuracy)} < {_pct(cfg.gate)} 门限）"


def render_report(m: Metrics, cfg: ReportConfig) -> str:
    pos, neg = cfg.positive_class, cfg.negative_class
    lines: List[str] = []
    lines.append(f"# {cfg.evaluator_label}评测报告")
    lines.append("")
    lines.append(f"> 生成时间：{cfg.timestamp}  ")
    lines.append(f"> 评估器：{cfg.evaluator_name}  ")
    lines.append(f"> 判定：{_verdict(m, cfg)}")
    lines.append("")

    # —— 配置 ——
    lines.append("## 配置")
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 评测模型 | {cfg.model_name} |")
    lines.append(f"| 决策阈值 | {cfg.threshold:.2f} |")
    lines.append(f"| 发布门限 | {_pct(cfg.gate)} |")
    lines.append(f"| 数据集 | {cfg.dataset_name} |")
    lines.append(f"| 样本数 | {m.n_total} |")
    lines.append("")

    # —— 核心指标 ——
    cm = m.confusion
    lines.append("## 核心指标")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 准确率 (correct/total) | {m.n_correct}/{m.n_total} = {_pct(m.accuracy)} |")
    lines.append(f"| 准确率 (仅判过) | {m.n_correct}/{m.n_judged} = {_pct(m.accuracy_among_judged)} |")
    lines.append(f"| 覆盖率 (judged/total) | {m.n_judged}/{m.n_total} = {_pct(m.coverage)} |")
    lines.append(f"| 错误样本数 | {m.n_errored} |")
    lines.append(f"| Precision ({pos}类) | {cm.precision:.3f} |")
    lines.append(f"| Recall ({pos}类) | {cm.recall:.3f} |")
    lines.append(f"| F1 | {cm.f1:.3f} |")
    lines.append("")

    # —— 混淆矩阵 ——
    lines.append(f"## 混淆矩阵（正类 = {pos}）")
    lines.append("")
    lines.append(f"|  | 预测{pos} | 预测{neg} |")
    lines.append("|---|---|---|")
    lines.append(f"| 实际{pos} | TP={cm.tp} | FN={cm.fn} |")
    lines.append(f"| 实际{neg} | FP={cm.fp} | TN={cm.tn} |")
    lines.append("")

    # —— 按样本类型分布 ——
    lines.append("## 按样本类型分布")
    lines.append("")
    lines.append("| 类型 | 总数 | 正确 | 错误样本 | 准确率 |")
    lines.append("|---|---|---|---|---|")
    order = ["positive", "strong_negative", "hard_negative"]
    for t in order:
        b = m.by_type.get(t)
        if b is None:
            continue
        lines.append(
            f"| {t} | {b.total} | {b.correct} | {b.errored} | {_pct(b.accuracy)} |"
        )
    for t, b in m.by_type.items():
        if t in order:
            continue
        lines.append(
            f"| {t} | {b.total} | {b.correct} | {b.errored} | {_pct(b.accuracy)} |"
        )
    lines.append("")

    # —— 逐样本明细（错误优先，再按 id）——
    lines.append("## 逐样本明细（错误优先）")
    lines.append("")
    lines.append("| id | 类型 | 金标 | 分数 | 预测 | 对错 | 理由 |")
    lines.append("|---|---|---|---|---|---|---|")
    ordered = sorted(
        m.results,
        key=lambda r: (r.correct, r.id),  # correct=False 排前面 (False<True)
    )
    for r in ordered:
        mark = "✓" if r.correct else "✗"
        reason = r.reason or ""
        if len(reason) > REASON_TRUNC:
            reason = reason[:REASON_TRUNC] + "…"
        lines.append(
            f"| {r.id} | {r.sample_type} | {r.label} | {_fmt_score(r.score)} | "
            f"{_fmt_pred(r.predicted, cfg)} | {mark} | {reason} |"
        )
    lines.append("")

    # —— 错误样本 ——
    if m.n_errored > 0:
        lines.append(f"## 错误样本（n={m.n_errored}）")
        lines.append("")
        for r in m.results:
            if r.judged:
                continue
            err = r.error or "(未知错误)"
            lines.append(f"- `{r.id}` [{r.sample_type}]：{err}")
        lines.append("")

    return "\n".join(lines)


def to_payload(m: Metrics, cfg: ReportConfig) -> Dict[str, Any]:
    """可序列化的完整结果，供 JSON 落盘复现/复查。"""
    cm = m.confusion
    return {
        "config": {
            "evaluator": cfg.evaluator_name,
            "evaluator_label": cfg.evaluator_label,
            "positive_class": cfg.positive_class,
            "negative_class": cfg.negative_class,
            "model_name": cfg.model_name,
            "threshold": cfg.threshold,
            "gate": cfg.gate,
            "dataset_name": cfg.dataset_name,
            "timestamp": cfg.timestamp,
        },
        "metrics": {
            "n_total": m.n_total,
            "n_judged": m.n_judged,
            "n_errored": m.n_errored,
            "n_correct": m.n_correct,
            "accuracy": m.accuracy,
            "accuracy_among_judged": m.accuracy_among_judged,
            "coverage": m.coverage,
            "precision": cm.precision,
            "recall": cm.recall,
            "f1": cm.f1,
            "confusion": {"tp": cm.tp, "fp": cm.fp, "fn": cm.fn, "tn": cm.tn},
            "by_type": {
                t: {
                    "total": b.total,
                    "correct": b.correct,
                    "errored": b.errored,
                    "accuracy": b.accuracy,
                }
                for t, b in m.by_type.items()
            },
            "passes_gate": m.passes_gate(cfg.gate),
        },
        "samples": [_sample_payload(r) for r in m.results],
    }


def _sample_payload(r: SampleResult) -> Dict[str, Any]:
    return {
        "id": r.id,
        "input": r.input,
        "output": r.output,
        "label": r.label,
        "sample_type": r.sample_type,
        "score": r.score,
        "predicted": r.predicted,
        "correct": r.correct,
        "threshold": r.threshold,
        "reason": r.reason,
        "error": r.error,
    }
