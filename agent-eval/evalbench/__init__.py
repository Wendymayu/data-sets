"""evalbench — 通用评估器实验工具。

把带金标的基准数据集喂给某个评估器（agenteval 的 metric，如
AnswerRelevanceMetric / GEval），把连续分数按阈值切成二分类预测，与金标
label 对比算准确率。准确率 >= 门限（默认 80%）视为该评估器可发布。

支持多评估器：在 profiles.py 注册一条档案（用哪个 metric、label 1/0 含义），
再丢一份同 schema 的基准 JSON 即可。详见 README「加一个评估器」。
"""

from evalbench.profiles import PROFILES, EvaluatorProfile, build_metric, get_profile
from evalbench.report import ReportConfig, render_report, to_payload
from evalbench.scoring import ConfusionMatrix, Metrics, SampleResult, TypeBreakdown

__all__ = [
    "PROFILES",
    "EvaluatorProfile",
    "build_metric",
    "get_profile",
    "ReportConfig",
    "render_report",
    "to_payload",
    "ConfusionMatrix",
    "Metrics",
    "SampleResult",
    "TypeBreakdown",
]
