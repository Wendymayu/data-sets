"""构建评测模型（与具体 metric 解耦）。

- 真实模型：``OpenAIModel``（agenteval 的 native 路径），从
  OPENAI_API_KEY / OPENAI_MODEL_NAME / OPENAI_BASE_URL / TEMPERATURE 取默认值，
  可被 CLI 覆盖。``base_url`` 兼容代理 / 本地 / 第三方 OpenAI 兼容端点。
- mock：``FixedScoreMock`` 固定返回某个分数，用于「不开网络也能跑通」的烟测，
  返回的准确率没有真实意义。

返回的是模型对象，交给具体评估器档案（profiles）去和某个 metric 绑定。
"""

from __future__ import annotations

import os
from typing import Optional

from agenteval import DeepEvalBaseLLM, EvaluationCost, OpenAIModel
from agenteval.metrics.g_eval.schema import ReasonScore


class FixedScoreMock(DeepEvalBaseLLM):
    """固定分数的假评测模型：无论输入都回同一个 score。

    和 agenteval 自带 AnswerRelevanceMock 同构：返回
    ``(ReasonScore, EvaluationCost)`` 元组，匹配 a_measure 的异步抽取路径，
    也匹配 GEval 无 logprobs 时的 fallback 路径。
    """

    def __init__(self, score: float = 1.0, model_name: str = "mock-fixed"):
        super().__init__(model=model_name)
        self._score = score
        self._name = model_name

    def load_model(self, *a, **k):
        return None

    def get_model_name(self, *a, **k):
        return self._name

    def generate(self, prompt, schema=None):
        return (
            ReasonScore(score=self._score, reason="fixed-score mock (dry-run)"),
            EvaluationCost(0.0, 0, 0),
        )

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema)


def build_model(
    *,
    mock: bool = False,
    mock_score: float = 1.0,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
) -> DeepEvalBaseLLM:
    """造评测模型。mock=True 返回固定分数假模型；否则 OpenAIModel（走 env/CLI）。"""
    if mock:
        return FixedScoreMock(score=mock_score)

    model_name = model_name or os.getenv("OPENAI_MODEL_NAME")  # None -> OpenAIModel 内部默认
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = base_url or os.getenv("OPENAI_BASE_URL")
    if temperature is None:
        t_env = os.getenv("TEMPERATURE")
        temperature = float(t_env) if t_env else None

    kwargs = {}
    if model_name is not None:
        kwargs["model"] = model_name
    if api_key is not None:
        kwargs["api_key"] = api_key
    if base_url is not None:
        kwargs["base_url"] = base_url
    if temperature is not None:
        kwargs["temperature"] = temperature

    return OpenAIModel(**kwargs)


def resolve_model_name(
    *,
    mock: bool = False,
    mock_score: float = 1.0,
    model_name: Optional[str] = None,
) -> str:
    """报告里显示的模型名（与 build_model 的选择保持一致）。"""
    if mock:
        return f"mock-fixed({mock_score})"
    return model_name or os.getenv("OPENAI_MODEL_NAME") or "openai-default"
