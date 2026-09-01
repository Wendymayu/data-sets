#!/usr/bin/env python
"""通用评估器实验工具入口。

把带金标的基准数据集喂给某个评估器（agenteval 的 metric），把连续分数按
阈值切成「正类/负类」二分类，与金标 label 对比算准确率。准确率达到 --gate
（默认 80%）视为该评估器可发布。每次跑都落一份 markdown 报告 + 原始 JSON。

典型用法：

  # 真实跑（需 OPENAI_API_KEY；可用 .env 配置，见下）
  python run_eval.py --evaluator relevance

  # 烟测脚手架本身（不开网络，mock 恒返回 1.0，准确率无意义，仅验证管线）
  python run_eval.py --evaluator relevance --mock

  # 调阈值 / 门限 / 限制条数快速试
  python run_eval.py --evaluator relevance --threshold 0.6 --gate 0.85 --limit 10

  # 自定义兼容端点（代理 / 本地 / 第三方 OpenAI 兼容服务）
  python run_eval.py --evaluator relevance --model gpt-4o-mini --base-url https://your-proxy/v1

  # 指向其它基准数据集（加新评估器后用）
  python run_eval.py --evaluator <新评估器> --data benchmarks/<名>/xxx.json

环境变量（优先级：CLI > shell 环境变量 > .env > 默认）：
  OPENAI_API_KEY      API key（真实跑必填）
  OPENAI_MODEL_NAME   模型名（默认走 agenteval 内置默认模型）
  OPENAI_BASE_URL     兼容端点
  TEMPERATURE         采样温度
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 让脚本可从任意 cwd 运行（把脚本目录加到 sys.path 以便 import evalbench）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evalbench.data import DEFAULT_DATA_PATH, load_samples  # noqa: E402
from evalbench.envfile import load_and_apply  # noqa: E402
from evalbench.harness import run  # noqa: E402
from evalbench.model import resolve_model_name  # noqa: E402
from evalbench.profiles import PROFILES, build_metric  # noqa: E402
from evalbench.report import ReportConfig, render_report, to_payload  # noqa: E402
from evalbench.scoring import DEFAULT_GATE, Metrics  # noqa: E402


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="通用评估器实验工具：在带金标基准上测准确率",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--evaluator",
        default="relevance",
        choices=sorted(PROFILES),
        help="评估器档案（在 evalbench/profiles.py 注册；新加评估器见 README）",
    )
    p.add_argument("--data", default=str(DEFAULT_DATA_PATH), help="基准 JSON 路径")
    p.add_argument("--threshold", type=float, default=0.5, help="分数切二分类的决策阈值")
    p.add_argument("--gate", type=float, default=DEFAULT_GATE, help="发布门限（准确率达标线）")
    p.add_argument("--model", default=None, help="模型名（默认走 OPENAI_MODEL_NAME / 内置）")
    p.add_argument("--base-url", default=None, help="OpenAI 兼容端点（默认走 OPENAI_BASE_URL）")
    p.add_argument("--api-key", default=None, help="API key（默认走 OPENAI_API_KEY）")
    p.add_argument("--temperature", type=float, default=None, help="采样温度")
    p.add_argument("--sync", action="store_true", help="同步串行跑（默认异步并发）")
    p.add_argument("--max-concurrent", type=int, default=20, help="异步并发上限")
    p.add_argument("--limit", type=int, default=None, help="只跑前 N 条（快速烟测）")
    p.add_argument("--out", default="reports", help="报告输出目录")
    p.add_argument("--env-file", default=".env", help="启动时自动加载的 .env 路径（不存在则跳过）")
    p.add_argument("--no-env", action="store_true", help="不自动加载 .env")
    p.add_argument("--mock", action="store_true", help="用固定分数 mock，不开网络（管线烟测）")
    p.add_argument("--mock-score", type=float, default=1.0, help="mock 固定分数")
    p.add_argument("--strict-exit", action="store_true", help="未达门限时以非 0 退出码结束（便于 CI）")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    _setup_console_io()  # 让 GBK 控制台不会因 emoji/特殊字符崩

    if not args.no_env:
        keys, envpath = load_and_apply(args.env_file)
        if envpath is not None:
            if keys:
                print(f"[eval] 加载 {envpath}: {', '.join(keys)}")
            else:
                print(f"[eval] 加载 {envpath}（全部已被环境变量覆盖，无新增）")

    samples = load_samples(args.data)
    if args.limit:
        samples = samples[: args.limit]

    model_display = resolve_model_name(
        mock=args.mock, mock_score=args.mock_score, model_name=args.model
    )
    print(
        f"[eval] 评估器: {args.evaluator}  样本数: {len(samples)}  模型: {model_display}  "
        f"阈值: {args.threshold}  门限: {args.gate:.2%}  mock: {args.mock}"
    )
    if not args.mock and not (args.api_key or _has_env("OPENAI_API_KEY")):
        print(
            "[eval] 警告：未设置 OPENAI_API_KEY，真实跑会失败。可用 --mock 先烟测脚手架。",
            file=sys.stderr,
        )

    profile, metric = build_metric(
        args.evaluator,
        threshold=args.threshold,
        mock=args.mock,
        mock_score=args.mock_score,
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        temperature=args.temperature,
        async_mode=not args.sync,
    )

    results = run(
        samples, metric, sync=args.sync, max_concurrent=args.max_concurrent, progress=True
    )
    m = Metrics(results)

    now = datetime.now()
    ts_file = now.strftime("%Y-%m-%d_%H%M%S")
    ts_disp = now.strftime("%Y-%m-%d %H:%M:%S")
    cfg = ReportConfig(
        model_name=model_display,
        threshold=args.threshold,
        gate=args.gate,
        dataset_name=Path(args.data).stem,
        timestamp=ts_disp,
        evaluator_name=type(metric).__name__,
        evaluator_label=profile.name,
        positive_class=profile.label1_meaning,
        negative_class=profile.label0_meaning,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = render_report(m, cfg)
    payload = to_payload(m, cfg)

    stem = out_dir / ts_file
    stem.with_suffix(".md").write_text(md, encoding="utf-8")
    stem.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "latest.md").write_text(md, encoding="utf-8")
    (out_dir / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    passed = m.passes_gate(args.gate)
    verdict = "通过（可发布）" if passed else "未通过"
    print(f"[eval] 准确率: {m.n_correct}/{m.n_total} = {m.accuracy:.2%}  判定: {verdict}")
    print(f"[eval] 报告: {stem.with_suffix('.md')}")
    print(f"[eval] 原始数据: {stem.with_suffix('.json')}")
    print(f"[eval] latest: {out_dir / 'latest.md'}")

    if args.strict_exit and not passed:
        return 1
    return 0


def _has_env(name: str) -> bool:
    import os

    return bool(os.getenv(name))


def _setup_console_io() -> None:
    """Windows 中文控制台默认 GBK 编码，遇到 emoji 会崩。把 stdout/stderr
    设成 errors='replace'，不可编码字符降级为 '?' 而非抛异常。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
