"""端到端联调：真实基准数据(60条) + 固定分数 mock（无网络）。

验证「加载 -> evaluate -> 回收分数 -> 评分 -> 报告」整条管线。mock 恒返回
score=1.0，所以所有样本被判为「相关」：20 条 positive 命中、40 条 negative
误判 -> 准确率 20/60。这些数字是确定可校验的。
"""

import json
from pathlib import Path

from evalbench.data import load_samples
from evalbench.harness import run
from evalbench.profiles import build_metric
from evalbench.report import ReportConfig, render_report, to_payload
from evalbench.scoring import Metrics

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "benchmarks"
    / "relevance"
    / "agent_relevance_evaluator_benchmark.json"
)


def test_load_real_benchmark():
    samples = load_samples(DATA_PATH)
    assert len(samples) == 60
    # 20 positive(label1) + 20 strong + 20 hard(label0)
    types = [s["sample_type"] for s in samples]
    assert types.count("positive") == 20
    assert types.count("strong_negative") == 20
    assert types.count("hard_negative") == 20
    assert all(s["label"] == 1 for s in samples if s["sample_type"] == "positive")
    assert all(s["label"] == 0 for s in samples if s["sample_type"] != "positive")


def test_e2e_full_pipeline_with_fixed_mock():
    samples = load_samples(DATA_PATH)
    _, metric = build_metric("relevance", threshold=0.5, mock=True, mock_score=1.0)
    results = run(samples, metric)

    assert len(results) == 60
    m = Metrics(results)
    assert m.n_total == 60
    assert m.n_judged == 60
    assert m.n_errored == 0
    assert m.n_correct == 20
    assert abs(m.accuracy - 20 / 60) < 1e-9

    cm = m.confusion
    assert (cm.tp, cm.fp, cm.fn, cm.tn) == (20, 40, 0, 0)
    assert abs(cm.precision - 1 / 3) < 1e-9
    assert cm.recall == 1.0
    assert abs(cm.f1 - 0.5) < 1e-9

    bt = m.by_type
    assert bt["positive"].accuracy == 1.0
    assert bt["strong_negative"].accuracy == 0.0
    assert bt["hard_negative"].accuracy == 0.0

    assert m.passes_gate(0.80) is False  # 33% < 80%


def test_e2e_report_and_payload():
    samples = load_samples(DATA_PATH)
    _, metric = build_metric("relevance", threshold=0.5, mock=True, mock_score=1.0)
    results = run(samples, metric)
    m = Metrics(results)
    cfg = ReportConfig(
        model_name="mock-fixed(1.0)",
        threshold=0.5,
        gate=0.80,
        dataset_name="agent-relevance-evaluator-benchmark",
        timestamp="2026-09-01 12:00:00",
    )
    md = render_report(m, cfg)
    assert "未通过" in md
    assert "33.33" in md  # accuracy
    payload = to_payload(m, cfg)
    json.dumps(payload, ensure_ascii=False)  # 可序列化
    assert payload["metrics"]["confusion"] == {"tp": 20, "fp": 40, "fn": 0, "tn": 0}
