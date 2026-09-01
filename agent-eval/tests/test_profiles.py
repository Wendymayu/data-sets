"""评估器档案注册表测试。"""

import pytest

from agenteval import AnswerRelevanceMetric

from evalbench.model import FixedScoreMock
from evalbench.profiles import PROFILES, EvaluatorProfile, build_metric, get_profile


def test_relevance_profile_registered():
    assert "relevance" in PROFILES
    p = get_profile("relevance")
    assert isinstance(p, EvaluatorProfile)
    assert p.key == "relevance"
    assert p.name == "相关性评估器"
    assert p.label1_meaning == "相关"
    assert p.label0_meaning == "不相关"


def test_unknown_profile_raises():
    with pytest.raises(KeyError):
        get_profile("nope")


def test_build_metric_relevance_mock():
    profile, metric = build_metric("relevance", threshold=0.5, mock=True, mock_score=1.0)
    assert profile.key == "relevance"
    assert isinstance(metric, AnswerRelevanceMetric)
    assert metric.threshold == 0.5
    assert metric.using_native_model is False  # FixedScoreMock 非 OpenAIModel


def test_build_metric_relevance_real_constructs_without_network():
    profile, metric = build_metric(
        "relevance", threshold=0.5, api_key="sk-test", model_name="gpt-4o-mini"
    )
    assert isinstance(metric, AnswerRelevanceMetric)
    assert metric.evaluation_model == "gpt-4o-mini"
    assert metric.using_native_model is True


def test_build_metric_returns_profile_for_report():
    # 报告需要 profile.name / profile.label1_meaning 做标题与混淆矩阵正类名
    profile, _ = build_metric("relevance", mock=True)
    assert profile.name  # 非空
    assert profile.label1_meaning
