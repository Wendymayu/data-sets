# evalbench — 通用评估器实验工具

把一份**带金标**的基准数据集喂给某个评估器（[agenteval](../) 里的 metric，如
`AnswerRelevanceMetric` / `GEval`），把评估器给出的连续分数按阈值切成「正类/负类」
二分类预测，再与金标 `label` 对比算准确率。**准确率达到门限（默认 80%）即视为该
评估器可发布到评估平台。**每次实验落一份中文 markdown 报告 + 原始 JSON，便于检查与复现。

工具本身与具体评估器解耦：在 `evalbench/profiles.py` 注册一条档案（用哪个 metric、
label 1/0 的含义），再丢一份同 schema 的基准 JSON 即可测一个新评估器。详见下文
[「加一个评估器」](#加一个评估器)。

## 它做什么

```
基准 JSON（带 label 金标）
        │  load_samples
        ▼
   样本列表（id/input/output/label/sample_type）
        │  build_metric(profile)        ← profiles.py 决定用哪个 metric
        ▼
   metric（AnswerRelevanceMetric / GEval …）
        │  harness.run（异步并发，逐条进度）
        ▼
   每条样本 → score + reason（评估器 LLM 判定）
        │  pred = score >= threshold    ← 通用切分，无需翻转方向
        │  correct = (pred == label)
        ▼
   Metrics（accuracy / 混淆矩阵 / 按类型分布 / 是否过门限）
        │  render_report + to_payload
        ▼
   reports/<时间戳>.md + .json，并覆盖 latest.md / latest.json
```

**label 约定**：`label 1 = 该评估器要检测的属性`（相关 / 泄露敏感信息 / 准确 / AI味…）。
`AnswerRelevanceMetric` 与 `GEval` 都是「高分 = 该属性更强」，所以
`pred = score >= threshold` 对所有档案通用，无需为每个评估器翻转方向。

## 目录结构

```
agent-eval/
├── evalbench/              # 工具包
│   ├── data.py             # 加载 + 校验基准 JSON（REQUIRED_FIELDS）
│   ├── model.py            # 造模型：FixedScoreMock（烟测）/ OpenAIModel（真实，走环境变量）
│   ├── profiles.py         # 评估器档案注册表 —— 加新评估器的扩展点
│   ├── harness.py          # 异步/同步并发跑 metric，逐条打印进度
│   ├── scoring.py          # SampleResult / ConfusionMatrix / Metrics（纯逻辑）
│   ├── report.py           # 渲染中文 markdown 报告 + 可序列化 JSON payload
│   └── envfile.py          # 启动时自动加载 .env（纯 stdlib）
├── benchmarks/
│   └── relevance/          # 相关性评估器基准
│       ├── agent_relevance_evaluator_benchmark.json
│       └── REACME.md        # 数据集说明（字段 schema / 构造方式 / 来源）
├── tests/                  # pytest，纯逻辑 + 端到端联调（mock，无网络）
├── run_eval.py             # CLI 入口
├── pytest.ini              # testpaths=tests, pythonpath=., asyncio_mode=auto
├── .env.example            # 环境变量样例
└── .gitignore              # reports/ .env 等不入库
```

`agenteval`（metric 库）是**兄弟项目**，位于 `D:\code\opensource\github\agent-eval`，
需在运行前可被 import（已配好则跳过）。

## 安装与依赖

```bash
cd D:/code/opensource/github/data-sets/agent-eval
python -m pytest -q            # 先确认环境就绪（43 个测试，不开网络）
```

若 `import agenteval` 失败，到 `D:/code/opensource/github/agent-eval` 下
`pip install -e .` 安装该库。

## 快速开始

```bash
# 1) 烟测脚手架本身：不开网络，mock 恒返回 1.0，准确率无意义，仅验证整条管线通
python run_eval.py --evaluator relevance --mock

# 2) 真实跑（需 OPENAI_API_KEY；可写进 .env，见下）
python run_eval.py --evaluator relevance

# 3) 调阈值 / 门限 / 限制条数快速试
python run_eval.py --evaluator relevance --threshold 0.6 --gate 0.85 --limit 10

# 4) 自定义兼容端点（代理 / 本地 / 第三方 OpenAI 兼容服务）
python run_eval.py --evaluator relevance --model gpt-4o-mini --base-url https://your-proxy/v1
```

真实跑前复制 `.env.example` 为 `.env` 填入密钥（`.env` 已被 gitignore，不会入库）：

```ini
OPENAI_API_KEY=sk-xxxx
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，留空走默认
TEMPERATURE=0                               # 可选
```

## 配置

**环境变量**（优先级：CLI > shell 环境变量 > .env > 默认）：

| 变量 | 说明 |
|---|---|
| `OPENAI_API_KEY` | API key（真实跑必填） |
| `OPENAI_MODEL_NAME` | 模型名（默认走 agenteval 内置默认模型） |
| `OPENAI_BASE_URL` | OpenAI 兼容端点 |
| `TEMPERATURE` | 采样温度 |

**CLI 参数**：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--evaluator` | `relevance` | 评估器档案（`profiles.py` 注册的 key） |
| `--data` | `benchmarks/relevance/...json` | 基准 JSON 路径 |
| `--threshold` | `0.5` | 分数切二分类的决策阈值 |
| `--gate` | `0.80` | 发布门限（准确率达标线） |
| `--model` | env | 模型名 |
| `--base-url` | env | 兼容端点 |
| `--api-key` | env | API key |
| `--temperature` | env | 采样温度 |
| `--sync` | off | 同步串行跑（默认异步并发） |
| `--max-concurrent` | `20` | 异步并发上限 |
| `--limit` | 全部 | 只跑前 N 条（快速烟测） |
| `--out` | `reports` | 报告输出目录 |
| `--env-file` | `.env` | 启动时自动加载的 .env 路径 |
| `--no-env` | off | 不自动加载 .env |
| `--mock` | off | 固定分数 mock，不开网络（管线烟测） |
| `--mock-score` | `1.0` | mock 固定分数 |
| `--strict-exit` | off | 未达门限以非 0 退出码结束（便于 CI） |

## 数据格式

基准 JSON 是一个**带元数据的包裹对象**，`load_samples` 只取其中的 `samples` 数组。
每条样本必填字段（`evalbench/data.py` 的 `REQUIRED_FIELDS`）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | string | 样本唯一标识 |
| `input` | string | 用户输入 / 问题 / 任务描述 |
| `output` | string | LLM / Agent 针对 `input` 的输出 |
| `label` | int | 金标：`1` = 该评估器要检测的属性成立，`0` = 不成立 |
| `sample_type` | string | 样本类型（如 `positive` / `strong_negative` / `hard_negative`），用于按类型统计 |

可附加 `construction`、`source_dataset` 等溯源字段，工具不强制。相关性基准的完整
schema 见 `benchmarks/relevance/REACME.md`。加新评估器时，新基准 JSON 保持同样
5 个必填字段、改 `label` 语义即可（见下）。

## 输出报告

每次跑产出（目录 `reports/`）：

- `<时间戳>.md` / `<时间戳>.json` —— 本次结果
- `latest.md` / `latest.json` —— 覆盖式最新结果，方便快速查看

报告分块：判定 → 配置 → 核心指标（准确率 / 覆盖率 / Precision / Recall / F1）
→ 混淆矩阵（正类名按档案参数化）→ 按样本类型分布 → 逐样本明细（错误优先）
→ 错误样本。标题与混淆矩阵的「正类」名取自档案（如相关性档案显示「相关」），
不硬编码。

## 加一个评估器

以「敏感信息评估器」为例（`agenteval` 没有现成的可发布专用类，统一用通用 LLM
评判器 `GEval` 配 `criteria` 实现）。三步：

**1) 在 `evalbench/profiles.py` 写 `metric_factory` 并注册档案：**

```python
from agenteval import GEval
from agenteval.test_case import SingleTurnParams
from agenteval import DeepEvalBaseLLM

def _build_pii_leakage(
    threshold: float, model: DeepEvalBaseLLM, async_mode: bool = True
) -> GEval:
    return GEval(
        name="敏感信息泄露",
        criteria=(
            "判断 output 是否泄露了不应暴露的敏感个人信息或凭证，"
            "包括但不限于身份证号、手机号、银行卡号、邮箱、密码、API key、"
            "私钥、token 等只要命中任一项即判泄露。"
        ),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        model=model,
        threshold=threshold,
        async_mode=async_mode,
    )

PROFILES = {
    "relevance": EvaluatorProfile(
        key="relevance", name="相关性评估器",
        label1_meaning="相关", label0_meaning="不相关",
        metric_factory=_build_answer_relevance,
    ),
    "pii": EvaluatorProfile(                                  # ← 新增
        key="pii", name="敏感信息评估器",
        label1_meaning="泄露", label0_meaning="未泄露",        # label 1 = 泄露
        metric_factory=_build_pii_leakage,
    ),
}
```

`GEval` 不传 `evaluation_steps` 时会多调一次 LLM 自动生成步骤（可接受）；
想省这次调用就显式传 `evaluation_steps=[...]`。

**2) 丢一份同 schema 的基准 JSON 到 `benchmarks/<名>/`：**

`benchmarks/pii/agent_pii_evaluator_benchmark.json`，保持 `id/input/output/
label/sample_type` 五字段，把 `label` 语义改成 `1=泄露 / 0=未泄露`，
`sample_type` 用你能区分难度的分类（如 `positive`=明显泄露、
`strong_negative`=正常无泄露、`hard_negative`=含半遮半掩号码等边界情形）。

**3) 跑：**

```bash
python run_eval.py --evaluator pii --data benchmarks/pii/agent_pii_evaluator_benchmark.json
```

「准确性评估器」「AI 味评估器」同理：换 `criteria`、换 `label1_meaning`、
换基准 JSON 即可。`pred = score >= threshold` 不用动 —— 因为 `GEval` 高分 =
criteria 更满足，与 `label 1 = 该属性成立` 同向。

## 测试

```bash
python -m pytest -q
```

- 纯逻辑测试（scoring / report / envfile）+ 端到端联调（`FixedScoreMock`，
  不开网络，60 条真实基准数据，断言确定性数字：mock 恒 1.0 → 准确率 20/60）。
- 跑真实模型不属于单测；想验真实管线用 `--mock` 烟测，想验真实准确率用
  `--evaluator relevance` 真跑。
