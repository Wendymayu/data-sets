"""把逐题结果写成 results.jsonl / summary.json / summary.md。

summary.md 含准确率、逐题表、失败模式分布；accuracy < low_score_threshold 时
附"得分过低原因"启发式分析（基于失败模式推断，非外部诊断）。
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _to_dict(r) -> dict:
    return asdict(r) if is_dataclass(r) else dict(r)


def _classify_failure(r, timeout: float | None) -> str:
    """把单个结果归类: correct / timeout / error / wrong。

    timeout = 未对 + 空模型答案 + 无显式错误（asyncio.TimeoutError 的 str() 为空）。
    error  = 未对 + 有错误信息。
    wrong  = 未对 + 有非空模型答案但与标准答案不符。
    """
    if getattr(r, "correct", False):
        return "correct"
    if getattr(r, "error", None) and str(r.error).strip():
        return "error"
    if not getattr(r, "prediction", ""):
        return "timeout"
    return "wrong"


def _md_cell(s, width: int = 40) -> str:
    s = str(s).replace("|", "\\|").replace("\n", " ").replace("\r", "")
    return s[:width]


def _build_summary_md(results, summary, meta, per_task_timeout, low_score_threshold) -> str:
    total = summary["total"]
    correct = summary["correct"]
    accuracy = summary["accuracy"]
    m = meta or {}
    lines = ["# GAIA → Twinkle 评测报告\n"]
    lines += [
        "| 项 | 值 |",
        "|---|---|",
        f"| 样本 | {_md_cell(m.get('samples',''))} |",
        f"| AgentServer | {_md_cell(m.get('agentserver_url',''))} |",
        f"| per-task-timeout | {per_task_timeout if per_task_timeout is not None else 'N/A'} s |",
        f"| 时间 | {_md_cell(m.get('timestamp',''))} |",
        f"| 任务数 | {total} |",
        f"| 正确 | {correct} |",
        f"| **准确率** | **{accuracy:.1%}** |",
    ]
    if summary.get("retried"):
        lines.append(
            f"| 重试 | 救回 {summary.get('recovered', 0)} / 重试 {summary.get('retried', 0)} |"
        )
    lines.append("")

    lines.append("## 逐题结果\n")
    lines.append("| task_id | 正确 | 重试 | 模型答案 | 标准答案 | 耗时(s) | 错误 |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        d = _to_dict(r)
        ok = "✓" if d.get("correct") else "✗"
        if d.get("recovered"):
            rt = "救回"
        elif d.get("retried"):
            rt = "仍败"
        else:
            rt = "—"
        lines.append(
            f"| {_md_cell(d.get('task_id',''), 24)} | {ok} | {rt} | "
            f"{_md_cell(d.get('prediction',''))} | {_md_cell(d.get('ground_truth',''))} | "
            f"{float(d.get('elapsed_s',0) or 0):.1f} | {_md_cell(d.get('error') or '')} |"
        )
    lines.append("")

    cats = Counter(_classify_failure(r, per_task_timeout) for r in results)
    lines.append("## 失败模式分布\n")
    for c in ("correct", "timeout", "error", "wrong"):
        lines.append(f"- {c}: {cats.get(c, 0)}")
    lines.append("")

    if total and accuracy < low_score_threshold:
        lines.append("## 得分过低原因分析\n")
        failed = total - correct
        lines.append(f"本轮 {correct}/{total} = {accuracy:.1%}，{failed} 题失败。")
        non_correct = {c: n for c, n in cats.items() if c != "correct"}
        if non_correct:
            dom = max(non_correct, key=non_correct.get)
            if dom == "timeout":
                lines.append(
                    "失败以**超时**为主：空模型答案、无显式错误、耗时接近 per-task-timeout。"
                    "通常意味着 twinkle 的 `web_search`/`web_fetch` 在当前网络或后端下"
                    "拿不到结果或过慢（例如 DuckDuckGo 反爬返回空）。建议：人工探 "
                    "`web_search` 是否返回空、网络是否受限，或调大 `--per-task-timeout`。"
                )
            elif dom == "error":
                errs = [str(r.error) for r in results if _classify_failure(r, per_task_timeout) == "error"]
                lines.append("失败以**报错**为主，top 错误：")
                for e, n in Counter(errs).most_common(3):
                    lines.append(f"  - ({n}×) {_md_cell(e, 80)}")
            else:  # wrong
                lines.append(
                    "失败以**答错**为主：agent 给出了非空模型答案但不等于标准答案。"
                    "多见于 model 推理/答案抽取不足，或 scorer 归一化过严；"
                    "建议抽查答错条目的模型答案与标准答案。"
                )
        lines.append("")

    return "\n".join(lines)


def write_report(
    results: list,
    output_dir: str,
    meta: dict | None = None,
    per_task_timeout: float | None = None,
    low_score_threshold: float = 0.5,
) -> dict:
    """写报告（results.jsonl / summary.json / summary.md），返回 summary dict。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    total = len(results)
    correct = sum(1 for r in results if getattr(r, "correct", False))
    accuracy = (correct / total) if total else 0.0
    retried = sum(1 for r in results if getattr(r, "retried", False))
    recovered = sum(1 for r in results if getattr(r, "recovered", False))
    summary = {"total": total, "correct": correct, "accuracy": accuracy,
               "retried": retried, "recovered": recovered}

    (out / "results.jsonl").write_text(
        "\n".join(json.dumps(_to_dict(r), ensure_ascii=False) for r in results) + ("\n" if results else ""),
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (out / "summary.md").write_text(
        _build_summary_md(results, summary, meta, per_task_timeout, low_score_threshold),
        encoding="utf-8",
    )

    return summary
