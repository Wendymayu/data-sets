import json
from pathlib import Path

from gaia_twinkle.runner import Sample, TaskResult, load_samples, extract_answer


def test_load_samples_reads_jsonl(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text(
        json.dumps({"task_id": "s1", "level": 1, "question": "q", "ground_truth": "Paris", "attachment": "a.csv"})
        + "\n"
        + json.dumps({"task_id": "s2", "question": "q2", "ground_truth": "Au"}) + "\n"
        + "# comment line\n"
        + "\n",
        encoding="utf-8",
    )
    samples = load_samples(f)
    assert len(samples) == 2
    assert samples[0].task_id == "s1"
    assert samples[0].level == 1
    assert samples[0].attachment == "a.csv"
    assert samples[1].level == 1  # default
    assert samples[1].attachment is None


def test_extract_answer_takes_last_nonempty_line():
    assert extract_answer("step 1\nstep 2\n\nParis") == "Paris"
    assert extract_answer("  Tokyo  ") == "Tokyo"
    assert extract_answer("") == ""


import asyncio
from gaia_twinkle.runner import run_task, run_all


class _StubClient:
    """假 client：按预设返回；记下收到的 query 与 session_id。"""
    def __init__(self, returns="Paris", raises=None):
        self.returns = returns
        self.raises = raises
        self.queries = []
        self.session_ids = []

    async def ask(self, query, session_id=None):
        self.queries.append(query)
        self.session_ids.append(session_id)
        if self.raises:
            raise self.raises
        return self.returns


def test_run_task_copies_attachment_and_scores(tmp_path):
    work = tmp_path / "ws"
    work.mkdir()
    attach = tmp_path / "att"
    attach.mkdir()
    (attach / "capitals.csv").write_text("country,capital\nJapan,Tokyo\n", encoding="utf-8")

    sample = Sample("s4", "capital of Japan per file?", "Tokyo", attachment="capitals.csv")
    client = _StubClient(returns="Tokyo")
    result = asyncio.run(run_task(sample, client, str(work), str(attach), timeout=5))

    assert result.correct is True
    assert result.prediction == "Tokyo"
    assert (work / "capitals.csv").exists()  # 附件已落入 workspace
    # query 含文件名提示 + 答案格式约束
    assert "capitals.csv" in client.queries[0]
    assert "只输出最终答案" in client.queries[0]


def test_run_task_wrong_answer_marked_wrong():
    sample = Sample("s1", "q", "Paris")
    client = _StubClient(returns="London")
    result = asyncio.run(run_task(sample, client, "/tmp/none", "/tmp/none", timeout=5))
    assert result.correct is False
    assert result.prediction == "London"


def test_run_task_records_error(tmp_path):
    from gaia_twinkle.twinkle_client import TwinkleError
    sample = Sample("s1", "q", "Paris")
    client = _StubClient(raises=TwinkleError("boom"))
    result = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path), timeout=5))
    assert result.correct is False
    assert "boom" in (result.error or "")


def test_run_all_parallel_preserves_order():
    golds = ["London", "Tokyo", "Paris", "Berlin", "Rome"]
    samples = [Sample(f"s{i}", "q", golds[i]) for i in range(5)]
    client = _StubClient(returns="42")  # 全返回 "42"，与各 gold 既不等也非子串 → 全错
    results = asyncio.run(run_all(samples, client, "/tmp/none", "/tmp/none", 5, concurrency=4))
    # 并发完成顺序不定，但结果按输入顺序返回
    assert [r.task_id for r in results] == [f"s{i}" for i in range(5)]
    assert all(r.prediction == "42" for r in results)
    assert all(r.correct is False for r in results)
    assert len(client.queries) == 5


def test_run_all_sequential_default():
    samples = [Sample(f"s{i}", "q", str(i)) for i in range(3)]
    client = _StubClient(returns="x")
    results = asyncio.run(run_all(samples, client, "/tmp/none", "/tmp/none", 5))
    assert [r.task_id for r in results] == ["s0", "s1", "s2"]


def test_run_task_passes_run_scoped_session_id(tmp_path):
    """每题 session_id 形如 <run_id>-<task_id>，不裸用 task_id（防续 twinkle 持久化历史）。"""
    sample = Sample("s1", "q", "Paris")
    client = _StubClient(returns="Paris")
    asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path), timeout=5, run_id="runX"))
    assert client.session_ids == ["runX-s1"]


def test_run_all_isolates_sessions_across_tasks():
    """同一 run 内各题 session_id 互不相同（task_id 不同 → session 不同）。"""
    samples = [Sample(f"s{i}", "q", str(i)) for i in range(3)]
    client = _StubClient(returns="x")
    asyncio.run(run_all(samples, client, "/tmp/none", "/tmp/none", 5, concurrency=1, run_id="runA"))
    assert len(set(client.session_ids)) == 3
    assert all(sid.startswith("runA-") for sid in client.session_ids)


def test_run_all_isolates_sessions_across_runs():
    """同一题在两次 run 里 session_id 不同（run_id 不同）→ 重跑不续旧账。"""
    sample = Sample("s1", "q", "Paris")
    c1 = _StubClient(returns="Paris")
    asyncio.run(run_all([sample], c1, "/tmp/none", "/tmp/none", 5, run_id="runA"))
    c2 = _StubClient(returns="Paris")
    asyncio.run(run_all([sample], c2, "/tmp/none", "/tmp/none", 5, run_id="runB"))
    assert c1.session_ids[0] == "runA-s1"
    assert c2.session_ids[0] == "runB-s1"
    assert c1.session_ids[0] != c2.session_ids[0]


# ---- 重试：只有"agent 没给出可用答案"（空 prediction = timeout/error）才重试一次 ----
# 设计判据：只有重试可解决的题才有重试的意义。wrong（非空答错）不重试（best-of-N 刷分）。
# 重试用全新 session_id（-r1 后缀）强制全新开局，否则会续上 twinkle 持久化的半截卡死 trace。

class _SeqClient:
    """按序列返回/抛出的假 client，记录每次 query 与 session_id。

    outcomes: list[str | Exception]，每次 ask 取下一个；str 返回，Exception 抛。
    """
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.queries = []
        self.session_ids = []

    async def ask(self, query, session_id=None):
        self.queries.append(query)
        self.session_ids.append(session_id)
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


def test_run_task_retries_on_empty_with_fresh_session_id(tmp_path):
    """首次空答案 → 重试 1 次 → 救回；重试用全新 session_id（-r1 后缀，不续旧 trace）。"""
    from gaia_twinkle.twinkle_client import TwinkleError  # noqa: F401（确认 import 路径可用）
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient(["", "Paris"])  # 首空 -> 重试 -> 对
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=1, run_id="runX"))
    assert r.correct is True
    assert r.prediction == "Paris"
    assert r.retried is True
    assert r.recovered is True
    assert len(client.session_ids) == 2
    assert client.session_ids[0] == "runX-s1"
    assert client.session_ids[1] == "runX-s1-r1"  # 全新 session，不裸用原 session_id


def test_run_task_persistent_empty_not_recovered(tmp_path):
    """首次空 -> 重试 -> 仍空：retried 但未 recovered，标 persistent infra 失败。"""
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient(["", ""])
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=1))
    assert r.retried is True
    assert r.recovered is False
    assert r.correct is False
    assert r.prediction == ""
    assert len(client.queries) == 2  # 重试了一次


def test_run_task_retry_returns_wrong_answer_not_recovered(tmp_path):
    """首空 -> 重试 -> 非空但错：retried、未 recovered、correct False，停（不再重试）。"""
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient(["", "London"])  # 重试给了答案但错
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=1))
    assert r.retried is True
    assert r.recovered is False
    assert r.correct is False
    assert r.prediction == "London"
    assert len(client.queries) == 2  # 拿到非空答案即停，不继续重试


def test_run_task_wrong_nonempty_not_retried(tmp_path):
    """非空答错（如 '$12,000' vs '16000'）不重试：不可重试，重试=刷分。"""
    sample = Sample("s1", "q", "16000")
    client = _SeqClient(["$12,000"])
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=1))
    assert r.retried is False
    assert r.correct is False
    assert len(client.queries) == 1


def test_run_task_retries_zero_disables_retry(tmp_path):
    """retries=0 = 关，单次诚实基线：即使空答案也不重试（保现状）。"""
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient([""])
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=0))
    assert r.retried is False
    assert r.correct is False
    assert len(client.queries) == 1


def test_run_task_correct_first_try_not_retried(tmp_path):
    """首次就对：不重试。"""
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient(["Paris"])
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=1))
    assert r.retried is False
    assert r.correct is True
    assert len(client.queries) == 1


def test_run_task_retries_on_error_then_succeeds(tmp_path):
    """error（无可用答案家族）也重试：首次抛错 -> 重试 -> 对 = recovered。"""
    from gaia_twinkle.twinkle_client import TwinkleError
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient([TwinkleError("boom"), "Paris"])
    r = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path),
                             timeout=5, retries=1, run_id="runX"))
    assert r.retried is True
    assert r.recovered is True
    assert r.correct is True
    assert client.session_ids[1].endswith("-r1")  # 重试用全新 session


def test_run_all_passes_retries_through():
    """run_all 把 retries 透传到 run_task。"""
    sample = Sample("s1", "q", "Paris")
    client = _SeqClient(["", "Paris"])
    results = asyncio.run(run_all([sample], client, "/tmp/none", "/tmp/none", 5,
                                  retries=1, run_id="runA"))
    assert len(results) == 1
    assert results[0].correct is True
    assert results[0].retried is True
    assert results[0].recovered is True
