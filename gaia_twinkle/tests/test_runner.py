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
    """假 client：按预设返回；记下收到的 query。"""
    def __init__(self, returns="Paris", raises=None):
        self.returns = returns
        self.raises = raises
        self.queries = []

    async def ask(self, query, session_id=None):
        self.queries.append(query)
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
