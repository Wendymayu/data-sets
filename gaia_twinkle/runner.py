"""样本加载 + 答案抽取 + 逐题执行编排。

编排：落附件进 workspace -> 构造 query -> 调 TwinkleClient -> 抽答案 -> 打分。
"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from gaia_twinkle.scorer import score


@dataclass
class Sample:
    task_id: str
    question: str
    ground_truth: str
    level: int = 1
    attachment: str | None = None
    hint: str | None = None


@dataclass
class TaskResult:
    task_id: str
    prediction: str
    ground_truth: str
    correct: bool
    error: str | None = None
    elapsed_s: float = 0.0


def load_samples(path: str | Path) -> list[Sample]:
    """读 jsonl，每行一个样本；跳过空行与 # 注释行。"""
    samples: list[Sample] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        d = json.loads(line)
        samples.append(Sample(
            task_id=d["task_id"],
            question=d["question"],
            ground_truth=d["ground_truth"],
            level=d.get("level", 1),
            attachment=d.get("attachment"),
            hint=d.get("hint"),
        ))
    return samples


def extract_answer(raw: str) -> str:
    """从 agent 原始输出抽短答案：strip；多行取最后一非空行。"""
    if not raw:
        return ""
    lines = [ln.strip() for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln]
    return lines[-1] if lines else ""


def _build_query(sample: Sample) -> str:
    q = sample.question.strip()
    if sample.attachment:
        q += f"\n\n文件 '{sample.attachment}' 已放入你的 workspace，可用 read_file 或 command_exec 查看。"
    if sample.hint:
        q += f"\n\n提示：{sample.hint}"
    q += "\n\n只输出最终答案，不要解释。"
    return q


async def run_task(
    sample: Sample,
    client,
    workspace_dir: str,
    attachments_dir: str,
    timeout: float,
) -> TaskResult:
    """跑一题：落附件 -> 构造 query -> 调 client -> 抽答案 -> 打分。"""
    start = time.monotonic()
    if sample.attachment:
        src = Path(attachments_dir) / sample.attachment
        dst = Path(workspace_dir) / sample.attachment
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    query = _build_query(sample)
    try:
        raw = await asyncio.wait_for(client.ask(query, session_id=sample.task_id), timeout=timeout)
        pred = extract_answer(raw)
        ok = score(pred, sample.ground_truth)
        return TaskResult(
            task_id=sample.task_id, prediction=pred,
            ground_truth=sample.ground_truth, correct=ok,
            elapsed_s=time.monotonic() - start,
        )
    except Exception as exc:
        return TaskResult(
            task_id=sample.task_id, prediction="",
            ground_truth=sample.ground_truth, correct=False,
            error=str(exc), elapsed_s=time.monotonic() - start,
        )


async def run_all(
    samples: list[Sample],
    client,
    workspace_dir: str,
    attachments_dir: str,
    timeout: float,
    on_result=None,
    concurrency: int = 1,
) -> list[TaskResult]:
    """跑全部样本。concurrency>1 时按信号量限流并发；结果按输入顺序返回。

    每题完成即调 on_result(result)（并发下完成顺序不定，但每条带 task_id 可辨）。
    假设：同一 workspace 下不同任务的附件文件名不冲突（GAIA 附件为 UUID 文件名，成立）。
    """
    sem = asyncio.Semaphore(max(1, int(concurrency)))

    async def _one(idx: int, s: Sample) -> tuple[int, TaskResult]:
        async with sem:
            r = await run_task(s, client, workspace_dir, attachments_dir, timeout)
            if on_result:
                on_result(r)
            return idx, r

    pairs = await asyncio.gather(*(_one(i, s) for i, s in enumerate(samples)))
    pairs.sort(key=lambda p: p[0])
    return [r for _, r in pairs]
