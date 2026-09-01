"""进度日志测试：跑 mock 时 stderr 应逐条打印进度行。"""

from pathlib import Path

from evalbench.data import load_samples
from evalbench.harness import run
from evalbench.profiles import build_metric

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "benchmarks"
    / "relevance"
    / "agent_relevance_evaluator_benchmark.json"
)


def test_progress_logs_to_stderr(capsys):
    samples = load_samples(DATA_PATH)[:5]
    _, metric = build_metric("relevance", threshold=0.5, mock=True, mock_score=1.0)
    results = run(samples, metric, progress=True)

    assert len(results) == 5
    err = capsys.readouterr().err
    # 最后一条应是 (5/5)
    assert "(5/5)" in err
    # 每条都带 id= 和 type=
    assert "id=" in err
    assert "type=" in err
    # 进度行数 == 样本数
    progress_lines = [ln for ln in err.splitlines() if "[rel-eval] (" in ln]
    assert len(progress_lines) == 5


def test_progress_off_by_default_is_quiet(capsys):
    samples = load_samples(DATA_PATH)[:3]
    _, metric = build_metric("relevance", threshold=0.5, mock=True, mock_score=1.0)
    run(samples, metric)  # progress 默认 False
    err = capsys.readouterr().err
    assert err == ""


def test_progress_async_concurrent_completes_all(capsys):
    # 默认异步并发，60 条全跑完，进度行数 == 60，结果数 == 60
    samples = load_samples(DATA_PATH)
    _, metric = build_metric("relevance", threshold=0.5, mock=True, mock_score=1.0)
    results = run(samples, metric, progress=True)
    assert len(results) == 60
    err = capsys.readouterr().err
    assert "(60/60)" in err
    assert len([ln for ln in err.splitlines() if "[rel-eval] (" in ln]) == 60
