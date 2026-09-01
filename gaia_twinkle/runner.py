"""样本加载 + 答案抽取 + 逐题执行编排。

编排：落附件进 workspace -> 构造 query -> 调 TwinkleClient -> 抽答案 -> 打分。
"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
import uuid
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
    retried: bool = False      # 是否重试过（首轮空答案才重试）
    recovered: bool = False    # 重试后救回（retried 且最终 correct）


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


def _session_id(run_id: str | None, task_id: str, attempt: int = 0) -> str:
    """合成每题每 run 独立的 session_id：``<run_id>-<task_id>[-r<attempt>]``。

    twinkle 的 SessionStore 按 session_id 在磁盘持久化对话历史，且 create_session
    幂等不清空——若裸用 task_id 作 session_id，重跑同一 eval-set 会续上上一次那题的
    整段 ReAct trace + 旧答案（agent 可能直接复述旧答案 → 飞轮信号失真）。故必须带
    run 级前缀：run 内各题 task_id 唯一 → session 不同；run 间 run_id 不同 → 不续旧账。
    run_id 缺省则现场生成短 uuid（仍保证每题独立，只是失去"一次 run 共前缀"的对账性）。

    重试时 attempt>0 追加 ``-r<attempt>`` 后缀：强制全新 session 开局，否则会续上
    首轮那条已卡死的半截 ReAct trace（尤其超时题卡在 web_search 上）→ 重试必再败。
    """
    rid = run_id or uuid.uuid4().hex[:8]
    sid = f"{rid}-{task_id}"
    if attempt:
        sid += f"-r{attempt}"
    return sid


async def _attempt(
    sample: Sample, client, query: str, timeout: float, session_id: str, start: float,
) -> TaskResult:
    """单次 ask：发 query、抽答案、打分。超时/异常 → 空 prediction + error。

    不含 retried/recovered（由 run_task 在编排重试后填）。
    """
    try:
        raw = await asyncio.wait_for(
            client.ask(query, session_id=session_id),
            timeout=timeout,
        )
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


async def run_task(
    sample: Sample,
    client,
    workspace_dir: str,
    attachments_dir: str,
    timeout: float,
    run_id: str | None = None,
    retries: int = 0,
) -> TaskResult:
    """跑一题：落附件 -> 构造 query -> 调 client -> 抽答案 -> 打分。

    session_id 由 (run_id, task_id) 合成，确保每题独立、重跑不续旧账。

    重试（retries>0）：只有"agent 没给出可用答案"（空 prediction = timeout/error）
    才重试——判据是"只有重试可解决的题才有重试的意义"。非空答错不重试（否则成
    best-of-N 刷分）。重试用全新 session_id（-r1 后缀）强制全新开局，不续首轮卡死的
    trace；一旦拿到非空答案即停（无论对错）。最终 retried/recovered 标在结果上，
    报告据此分开"救回"与"persistent infra 失败"，不静默涨分。
    """
    start = time.monotonic()
    if sample.attachment:
        src = Path(attachments_dir) / sample.attachment
        dst = Path(workspace_dir) / sample.attachment
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    query = _build_query(sample)

    r = await _attempt(sample, client, query, timeout,
                       _session_id(run_id, sample.task_id), start)
    retried = False
    attempt = 0
    while retries > 0 and not r.prediction:
        retried = True
        attempt += 1
        r = await _attempt(sample, client, query, timeout,
                           _session_id(run_id, sample.task_id, attempt), start)
        retries -= 1
    r.retried = retried
    r.recovered = retried and r.correct
    return r


async def run_all(
    samples: list[Sample],
    client,
    workspace_dir: str,
    attachments_dir: str,
    timeout: float,
    on_result=None,
    concurrency: int = 1,
    run_id: str | None = None,
    retries: int = 0,
) -> list[TaskResult]:
    """跑全部样本。concurrency>1 时按信号量限流并发；结果按输入顺序返回。

    每题完成即调 on_result(result)（并发下完成顺序不定，但每条带 task_id 可辨）。
    假设：同一 workspace 下不同任务的附件文件名不冲突（GAIA 附件为 UUID 文件名，成立）。

    run_id 作为本次 run 的 session 前缀（缺省则现场生成一个）：所有题共享此前缀，
    便于从 twinkle sessions 目录反查回本次 run；前缀 + task_id 保证每题 session 独立。

    retries 透传给 run_task（每题空答案最多重试 retries 次）。
    """
    run_id = run_id or uuid.uuid4().hex[:8]
    sem = asyncio.Semaphore(max(1, int(concurrency)))

    async def _one(idx: int, s: Sample) -> tuple[int, TaskResult]:
        async with sem:
            r = await run_task(s, client, workspace_dir, attachments_dir, timeout,
                               run_id=run_id, retries=retries)
            if on_result:
                on_result(r)
            return idx, r

    pairs = await asyncio.gather(*(_one(i, s) for i, s in enumerate(samples)))
    pairs.sort(key=lambda p: p[0])
    return [r for _, r in pairs]
