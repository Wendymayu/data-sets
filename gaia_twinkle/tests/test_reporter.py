import json
from dataclasses import dataclass

from gaia_twinkle.reporter import write_report


@dataclass
class R:
    task_id: str
    prediction: str
    ground_truth: str
    correct: bool
    error: str | None = None
    elapsed_s: float = 0.0
    retried: bool = False
    recovered: bool = False


def test_write_report_outputs_files_and_summary(tmp_path):
    results = [
        R("s1", "Paris", "Paris", True),
        R("s2", "London", "Au", False, error="timeout"),
    ]
    summary = write_report(results, str(tmp_path))
    assert summary == {"total": 2, "correct": 1, "accuracy": 0.5,
                       "retried": 0, "recovered": 0}

    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "results.jsonl").exists()
    assert not (tmp_path / "summary.txt").exists()  # 已移除 summary.txt，只留 summary.md
    assert (tmp_path / "summary.md").exists()

    sj = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert sj["accuracy"] == 0.5
    assert sj["retried"] == 0
    assert sj["recovered"] == 0

    lines = (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["task_id"] == "s1"


def test_summary_md_retry_transparency(tmp_path):
    """有重试时：summary 带计数、md 顶部一行统计、逐题表标 救回/仍败/—。不静默涨分。"""
    results = [
        R("s1", "Paris", "Paris", True),                                   # 首次对，未重试
        R("s2", "Paris", "Paris", True, retried=True, recovered=True),     # 救回
        R("s3", "", "17", False, retried=True, recovered=False),           # 重试仍败
    ]
    summary = write_report(results, str(tmp_path))
    assert summary["accuracy"] == 2 / 3
    assert summary["retried"] == 2
    assert summary["recovered"] == 1
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "救回 1 / 重试 2" in md   # 顶部统计行
    assert "仍败" in md             # s3 逐题标记
    assert "救回" in md             # s2 逐题标记
    # results.jsonl 也带重试字段
    rows = [json.loads(l) for l in (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[1]["retried"] is True and rows[1]["recovered"] is True
    assert rows[2]["retried"] is True and rows[2]["recovered"] is False
    assert rows[0]["retried"] is False


def test_summary_md_no_retry_section_when_none_retried(tmp_path):
    """无重试（--retries 0 基线）：不出现救回/仍败标记，不刷存在感。"""
    results = [R("s1", "Paris", "Paris", True), R("s2", "Au", "Au", True)]
    write_report(results, str(tmp_path))
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "救回" not in md
    assert "仍败" not in md


def test_summary_md_low_score_analysis(tmp_path):
    results = [
        R("s1", "Paris", "Paris", True, elapsed_s=2.0),
        R("s2", "", "17", False, error="", elapsed_s=60.0),    # timeout (TimeoutError str is "")
        R("s3", "", "3", False, error="boom", elapsed_s=3.0),  # error
        R("s4", "London", "Au", False, elapsed_s=5.0),          # wrong (non-empty pred)
    ]
    summary = write_report(results, str(tmp_path), per_task_timeout=60.0,
                           meta={"samples": "x.jsonl", "agentserver_url": "ws://x:1", "timestamp": "t"})
    assert summary["accuracy"] == 0.25
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "25.0%" in md
    assert "失败模式" in md
    assert "timeout: 1" in md
    assert "error: 1" in md
    assert "wrong: 1" in md
    assert "得分过低" in md          # low-score section (25% < 50%)
    assert "超时" in md              # timeout narrative
    assert "boom" in md             # error surfaced in per-task table
    assert "ws://x:1" in md         # meta in header


def test_summary_md_no_low_score_section_when_high(tmp_path):
    results = [R("s1", "Paris", "Paris", True), R("s2", "Au", "Au", True)]
    write_report(results, str(tmp_path))
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "得分过低" not in md     # high score -> no low-score section
    assert "100.0%" in md
