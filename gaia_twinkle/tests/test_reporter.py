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


def test_write_report_outputs_files_and_summary(tmp_path):
    results = [
        R("s1", "Paris", "Paris", True),
        R("s2", "London", "Au", False, error="timeout"),
    ]
    summary = write_report(results, str(tmp_path))
    assert summary == {"total": 2, "correct": 1, "accuracy": 0.5}

    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "results.jsonl").exists()
    assert not (tmp_path / "summary.txt").exists()  # 已移除 summary.txt，只留 summary.md
    assert (tmp_path / "summary.md").exists()

    sj = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert sj["accuracy"] == 0.5

    lines = (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["task_id"] == "s1"


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
