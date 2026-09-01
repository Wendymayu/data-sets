"""评估器档案注册表 —— 通用框架的扩展点。

每条档案 = 一个评估器：它用哪个 agenteval metric、label 1 / 0 的含义。
加一个新评估器：写一个 ``metric_factory``（通常用 ``GEval`` 配 criteria），
在这里注册一条，再丢一份同 schema 的基准 JSON。详见 README「加一个评估器」。

约定：``label 1 = 该评估器要检测的属性``（相关 / 泄露敏感信息 / 准确 / AI味…）。
``AnswerRelevanceMetric`` 与 ``GEval`` 都是「高分 = 该属性更强」，所以
``pred = score >= threshold`` 对所有档案通用，无需翻转方向。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from agenteval import AnswerRelevanceMetric, DeepEvalBaseLLM

from evalbench.model import build_model


@dataclass(frozen=True)
class EvaluatorProfile:
    """一个评估器的描述。"""

    key: str  # 'relevance'
    name: str  # '相关性评估器' —— 报告标题用
    label1_meaning: str  # '相关' —— label 1 含义，混淆矩阵「正类」名
    label0_meaning: str  # '不相关'
    metric_factory: Callable[..., object]  # (threshold, model, async_mode) -> BaseMetric


def _build_answer_relevance(
    threshold: float, model: DeepEvalBaseLLM, async_mode: bool = True
) -> AnswerRelevanceMetric:
    return AnswerRelevanceMetric(
        model=model, threshold=threshold, async_mode=async_mode
    )


PROFILES: Dict[str, EvaluatorProfile] = {
    "relevance": EvaluatorProfile(
        key="relevance",
        name="相关性评估器",
        label1_meaning="相关",
        label0_meaning="不相关",
        metric_factory=_build_answer_relevance,
    ),
}


def get_profile(key: str) -> EvaluatorProfile:
    if key not in PROFILES:
        raise KeyError(f"未知评估器 {key!r}，已注册: {sorted(PROFILES)}")
    return PROFILES[key]


def build_metric(
    profile_key: str,
    *,
    threshold: float = 0.5,
    mock: bool = False,
    mock_score: float = 1.0,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    async_mode: bool = True,
) -> Tuple[EvaluatorProfile, object]:
    """造 (profile, metric)：profile 供报告取标题/label 含义，metric 供 harness 跑。"""
    profile = get_profile(profile_key)
    model = build_model(
        mock=mock,
        mock_score=mock_score,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )
    metric = profile.metric_factory(
        threshold=threshold, model=model, async_mode=async_mode
    )
    return profile, metric
