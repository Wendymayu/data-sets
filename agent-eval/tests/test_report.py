"""报告渲染测试：用固定 fixture 验证 markdown / json 结构，无 LLM。"""

import json

from evalbench.report import ReportConfig, render_report, to_payload
from evalbench.scoring import Metrics, SampleResult


def _fx() -> Metrics:
    return Metrics(
        [
            SampleResult("p1", "i1", "o1", 1, "positive", 0.9, threshold=0.5, reason="on topic"),
            SampleResult("p2", "i2", "o2", 1, "positive", 0.4, threshold=0.5, reason="off topic"),
            SampleResult(
                "p3", "i3", "o3", 1, "positive", None, threshold=0.5, error="judge crashed"
            ),
            SampleResult("s1", "i4", "o4", 0, "strong_negative", 0.1, threshold=0.5, reason="unrelated"),
            SampleResult("s2", "i5", "o5", 0, "strong_negative", 0.8, threshold=0.5, reason="foo"),
            SampleResult("h1", "i6", "o6", 0, "hard_negative", 0.55, threshold=0.5, reason="related but no answer"),
            SampleResult("h2", "i7", "o7", 0, "hard_negative", 0.2, threshold=0.5, reason="bar"),
        ]
    )


def _cfg() -> ReportConfig:
    return ReportConfig(
        model_name="gpt-4o-mini",
        threshold=0.5,
        gate=0.80,
        dataset_name="agent-relevance-evaluator-benchmark",
        timestamp="2026-09-01 12:00:00",
    )


def test_report_has_title_and_timestamp():
    md = render_report(_fx(), _cfg())
    assert "相关性评估器评测报告" in md
    assert "2026-09-01 12:00:00" in md


def test_report_shows_fail_verdict_when_below_gate():
    # accuracy=3/7≈0.4286 < 0.80
    md = render_report(_fx(), _cfg())
    assert "未通过" in md
    assert "❌" in md
    assert "✅" not in md


def test_report_shows_pass_verdict_when_above_gate():
    m = Metrics(
        [
            SampleResult("p", "i", "o", 1, "positive", 1.0, threshold=0.5),
            SampleResult("n", "i", "o", 0, "hard_negative", 0.0, threshold=0.5),
        ]
    )
    md = render_report(m, _cfg())
    assert "✅" in md
    assert "通过" in md
    assert "未通过" not in md
    assert "❌" not in md


def test_report_contains_config_block():
    md = render_report(_fx(), _cfg())
    assert "gpt-4o-mini" in md
    assert "0.50" in md  # threshold
    assert "80" in md  # gate
    assert "agent-relevance-evaluator-benchmark" in md


def test_report_contains_headline_metrics():
    md = render_report(_fx(), _cfg())
    assert "准确率" in md
    assert "42.86" in md  # 3/7 -> 42.86%
    assert "覆盖率" in md
    assert "Precision" in md
    assert "Recall" in md
    assert "F1" in md


def test_report_contains_confusion_matrix():
    md = render_report(_fx(), _cfg())
    assert "混淆矩阵" in md
    # tp1 fp2 fn1 tn2
    assert "TP" in md and "FP" in md and "FN" in md and "TN" in md
    assert "1" in md and "2" in md


def test_report_contains_per_type_breakdown():
    md = render_report(_fx(), _cfg())
    assert "positive" in md
    assert "strong_negative" in md
    assert "hard_negative" in md
    # 每类都该出现准确率
    assert "33.33" in md  # positive 1/3
    assert "50.00" in md  # strong/hard 1/2


def test_report_lists_wrong_samples_first_in_detail():
    md = render_report(_fx(), _cfg())
    assert "逐样本明细" in md
    # 错的样本 id 应出现
    assert "p2" in md and "s2" in md and "h1" in md
    # 错的排在前面：p2 的位置应在 h2（对的那条）之前
    assert md.index("p2") < md.index("h2")


def test_report_includes_error_section_when_errors_present():
    md = render_report(_fx(), _cfg())
    assert "## 错误样本（n=" in md
    assert "p3" in md
    assert "judge crashed" in md


def test_report_no_error_section_when_clean():
    m = Metrics(
        [
            SampleResult("p", "i", "o", 1, "positive", 0.9, threshold=0.5),
            SampleResult("n", "i", "o", 0, "strong_negative", 0.1, threshold=0.5),
        ]
    )
    md = render_report(m, _cfg())
    assert "## 错误样本" not in md


def test_to_payload_structure():
    payload = to_payload(_fx(), _cfg())
    assert payload["config"]["model_name"] == "gpt-4o-mini"
    assert payload["metrics"]["n_total"] == 7
    assert payload["metrics"]["n_correct"] == 3
    assert abs(payload["metrics"]["accuracy"] - 3 / 7) < 1e-9
    assert payload["metrics"]["confusion"] == {"tp": 1, "fp": 2, "fn": 1, "tn": 2}
    assert len(payload["samples"]) == 7
    s = payload["samples"][0]
    assert set(s.keys()) >= {"id", "sample_type", "label", "score", "predicted", "correct"}
    # json 可序列化
    json.dumps(payload, ensure_ascii=False)
