"""编排：把基准样本喂给评估器，回收每条分数，组装 SampleResult。

不直接用 ``agenteval.evaluate`` 的黑盒批量接口（它没有进度回调），而是自己跑
一个并发循环：每条用 ``copy_metrics`` 复制一份 metric（避免并发复用同一实例
造成 self.score 竞态），单条异常吞到 ``metric.error``（不拖垮整批），每跑完
一条往 stderr 打一行进度。sync 模式串行，async 模式信号量限并发。
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Dict, List

from agenteval import LLMTestCase
from agenteval.errors import AgentEvalError
from agenteval.metrics.utils import copy_metrics
from agenteval.utils import get_or_create_event_loop

from evalbench.scoring import SampleResult


def run(
    samples: List[Dict[str, Any]],
    metric,
    *,
    sync: bool = False,
    max_concurrent: int = 20,
    progress: bool = False,
) -> List[SampleResult]:
    """跑完所有样本，返回与输入同序的 SampleResult 列表。

    ``progress=True`` 时每条完成往 stderr 打一行（默认 False，便于库式调用/测试）。
    """
    threshold = metric.threshold
    if sync:
        return _run_sync(samples, metric, threshold, progress)
    return _run_async(samples, metric, threshold, max_concurrent, progress)


def _make_result(sample: Dict[str, Any], m, threshold: float) -> SampleResult:
    return SampleResult(
        id=sample["id"],
        input=sample["input"],
        output=sample["output"],
        label=sample["label"],
        sample_type=sample["sample_type"],
        score=getattr(m, "score", None),
        threshold=threshold,
        reason=getattr(m, "reason", None),
        error=getattr(m, "error", None),
    )


def _eval_metric_sync(m, test_case) -> None:
    """sync 跑 measure；任何异常记到 m.error，不外抛。"""
    try:
        m.measure(test_case, _show_indicator=False)
    except AgentEvalError as e:
        m.error = str(e)
        m.success = False
    except Exception as e:  # 网络/解析/超时等，单条失败不影响整批
        m.error = f"{type(e).__name__}: {e}"
        m.success = False


async def _eval_metric_async(m, test_case) -> None:
    """async 跑 a_measure；任何异常记到 m.error，不外抛。"""
    try:
        await m.a_measure(test_case, _show_indicator=False)
    except AgentEvalError as e:
        m.error = str(e)
        m.success = False
    except Exception as e:  # 网络/解析/超时等，单条失败不影响整批
        m.error = f"{type(e).__name__}: {e}"
        m.success = False


def _print_progress(done: int, total: int, r: SampleResult, correct: int) -> None:
    # 全 ASCII：进度行要在任意控制台编码下都可读（GBK/UTF-8 都不崩不乱码）。
    score_s = f"{r.score:.2f}" if r.score is not None else "n/a"
    if r.predicted is None:
        pred_s = "ERR"
    else:
        pred_s = "REL" if r.predicted == 1 else "IRREL"
    mark = "OK" if r.correct else "MISS"
    sys.stderr.write(
        f"[rel-eval] ({done}/{total}) id={r.id} type={r.sample_type} "
        f"score={score_s} pred={pred_s} {mark} | ok {correct}/{done}\n"
    )
    sys.stderr.flush()


def _run_sync(samples, metric, threshold, progress) -> List[SampleResult]:
    out: List[SampleResult] = []
    done = correct = 0
    total = len(samples)
    for s in samples:
        m = copy_metrics([metric])[0]
        tc = LLMTestCase(input=s["input"], actual_output=s["output"])
        _eval_metric_sync(m, tc)
        r = _make_result(s, m, threshold)
        done += 1
        if r.correct:
            correct += 1
        if progress:
            _print_progress(done, total, r, correct)
        out.append(r)
    return out


def _run_async(samples, metric, threshold, max_concurrent, progress) -> List[SampleResult]:
    total = len(samples)
    counter = {"done": 0, "correct": 0}

    async def one(s):
        m = copy_metrics([metric])[0]
        tc = LLMTestCase(input=s["input"], actual_output=s["output"])
        await _eval_metric_async(m, tc)
        r = _make_result(s, m, threshold)
        counter["done"] += 1
        if r.correct:
            counter["correct"] += 1
        if progress:
            _print_progress(counter["done"], total, r, counter["correct"])
        return r

    async def runner():
        sem = asyncio.Semaphore(max_concurrent)

        async def bounded(s):
            async with sem:
                return await one(s)

        return await asyncio.gather(*(bounded(s) for s in samples))

    loop = get_or_create_event_loop()
    results = loop.run_until_complete(runner())
    return results
