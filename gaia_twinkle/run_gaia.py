"""CLI：加载样本 -> 连 twinkle -> 逐题跑 -> 打分 -> 写报告。"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import os
import sys
from pathlib import Path

from gaia_twinkle.reporter import write_report
from gaia_twinkle.runner import load_samples, run_all
from gaia_twinkle.twinkle_client import TwinkleClient

# 命名评测集预设：tasks + 附件目录。
# smoke=手造假样本（无需 gated 数据，可提交）；
# easy/medium/hard=GAIA L1/L2/L3 无附件（难度三档，gitignore）；
# attachments=GAIA 带附件题（任意 level，测文件路径，gitignore）。
EVAL_SETS = {
    "smoke": {
        "samples": "gaia_twinkle/data/smoke/tasks.jsonl",
        "attachments": "gaia_twinkle/data/smoke/attachments",
    },
    "easy": {
        "samples": "gaia_twinkle/data/easy/tasks.jsonl",
        "attachments": "gaia_twinkle/data/gaia/2023/validation",
    },
    "medium": {
        "samples": "gaia_twinkle/data/medium/tasks.jsonl",
        "attachments": "gaia_twinkle/data/gaia/2023/validation",
    },
    "hard": {
        "samples": "gaia_twinkle/data/hard/tasks.jsonl",
        "attachments": "gaia_twinkle/data/gaia/2023/validation",
    },
    "attachments": {
        "samples": "gaia_twinkle/data/attachments/tasks.jsonl",
        "attachments": "gaia_twinkle/data/gaia/2023/validation",
    },
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GAIA-style eval harness for twinkle.")
    p.add_argument("--eval-set", choices=sorted(EVAL_SETS), default=None,
                   help="named eval set: smoke / easy / medium / hard / attachments")
    p.add_argument("--agentserver-url", default=os.environ.get(
        "TWINKLE_AGENTSERVER_URL", "ws://127.0.0.1:18000"))
    p.add_argument("--workspace-dir", default=os.environ.get(
        "TWINKLE_WORKSPACE_DIR", str(Path.home() / ".twinkle")))
    p.add_argument("--samples", default=EVAL_SETS["smoke"]["samples"],
                   help="tasks jsonl (ignored if --eval-set given)")
    p.add_argument("--attachments-dir", default=EVAL_SETS["smoke"]["attachments"],
                   help="attachments dir (ignored if --eval-set given)")
    p.add_argument("--per-task-timeout", type=float, default=300.0)
    p.add_argument("--concurrency", type=int, default=4,
                   help="并发任务数（默认 4；受 LLM 限流制约，过高易 429）")
    p.add_argument("--limit", type=int, default=None, help="cap number of tasks (quick run)")
    p.add_argument("--output", default=None)
    return p


def apply_eval_set(args) -> None:
    """若指定 --eval-set，用预设覆盖 samples / attachments-dir。"""
    if args.eval_set:
        cfg = EVAL_SETS[args.eval_set]
        args.samples = cfg["samples"]
        args.attachments_dir = cfg["attachments"]


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to the system codepage (e.g. GBK), which can't
    # encode ✓/✗ or non-ASCII predictions → force UTF-8 to avoid crashes.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = build_parser().parse_args(argv)
    apply_eval_set(args)

    samples = load_samples(args.samples)
    if not samples:
        print(f"no samples loaded from {args.samples}", file=sys.stderr)
        return 2
    if args.limit:
        samples = samples[:args.limit]

    client = TwinkleClient(args.agentserver_url, timeout=args.per_task_timeout)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = args.output or f"gaia_twinkle/output/{ts}"

    total_n = len(samples)
    done = [0]

    def on_result(r) -> None:
        done[0] += 1
        flag = "✓" if r.correct else "✗"
        print(f"[{done[0]}/{total_n}] {flag} {r.task_id}: "
              f"模型答案={r.prediction!r} 标准答案={r.ground_truth!r} {r.error or ''}")

    Path(args.workspace_dir).mkdir(parents=True, exist_ok=True)
    results = asyncio.run(run_all(
        samples, client, args.workspace_dir, args.attachments_dir,
        args.per_task_timeout, on_result, args.concurrency,
    ))

    summary = write_report(
        results, out_dir,
        meta={"samples": args.samples, "agentserver_url": args.agentserver_url, "timestamp": ts},
        per_task_timeout=args.per_task_timeout,
    )
    print(f"\naccuracy: {summary['correct']}/{summary['total']} = {summary['accuracy']:.1%}")
    print(f"report: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
