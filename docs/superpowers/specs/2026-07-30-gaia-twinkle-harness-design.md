# GAIA → Twinkle 评测 Harness 设计（基础版）

- 日期：2026-07-30
- 状态：已与用户确认设计，待 spec review → 转 writing-plans
- 相关仓库：harness 放 `data-sets`（当前仓库）；被测对象为 `D:\code\opensource\github\twinkle`

## 1. 背景与目标

为 twinkle（ReAct agent，WebSocket 接口）实现一个**基础版** GAIA 风格评测 harness：用本地 mini 样本（GAIA 形状）驱动 twinkle 答题，对输出做归一化精确匹配打分，产出准确率报告。

**为什么是"基础版"**：GAIA 数据集在 HuggingFace 上是 gated（需登录 + 接受协议 + token），且本机访问 HF / token / 授权均未就绪。故先用本地样本把全链路（加载 → WS 发问 → 收答案 → 打分 → 报告）跑通，数据加载器做成可替换接口；真实 GAIA 数据到位后只替换 loader，不动 harness 主体与打分逻辑。

## 2. 非目标（YAGNI，首版明确不做）

- 并发 / 多任务并行（首版顺序跑）
- 真实 GAIA 数据 loader（首版用本地样本）
- LLM 答案抽取 / LLM judge（首版用 prompt 约束 + 启发式）
- 二进制附件解析（PDF / xlsx / 图片 / 音频——twinkle 已知能力缺口，首版样本只用 `read_file` 能读的文本格式）
- GAIA 榜单提交格式

## 3. 方案选型

方案 A（已选）：harness 放 **data-sets 仓库**，独立 WS 客户端，仅依赖 `websockets`，不 import twinkle 任何代码。信封 / 帧手搓 JSON。运行用 twinkle venv python（已含 `websockets`）或任何装了 `websockets` 的 python。

否掉的备选：
- B（放 twinkle 仓库、复用 `E2AEnvelope` 模型）——eval harness 混进 agent 仓库，与 twinkle 聚焦 agent 本体的定位不搭。
- C（走 gateway / 浏览器通道而非直连 AgentServer）——gateway 是给浏览器做格式翻译的，harness 走它白多一层浏览器帧协议，无收益。直连 AgentServer 的 E2A 是最干净的控制面。

## 4. 架构与数据流

```
mini_gaia.jsonl → loader → runner(WS client → AgentServer) → answer 提取 → scorer → reporter → output/<timestamp>/
```

- **loader**：读 jsonl，逐条产出 Sample（`task_id` / `level` / `question` / `ground_truth` / `attachment` / `hint`）。
- **runner**：对每个 Sample，必要时把附件拷进 twinkle workspace；构造 query（问题 + 答案格式指令）；WS 连 AgentServer，发 E2AEnvelope，读到 final 取文本。
- **answer 提取**：取 final content，strip；多行取最后一非空行。
- **scorer**：归一化 + 精确 / 子串匹配，判 pass / fail。
- **reporter**：逐题结果 JSON + 汇总（准确率、逐题 pass/fail、耗时、失败原因）。

## 5. 组件（`data-sets/gaia-twinkle/`）

| 文件 | 职责 | 依赖 |
|---|---|---|
| `twinkle_client.py` | WS 客户端：连 AgentServer，发 `E2AEnvelope(method="chat.send", params={"query":...})`，读帧到 `e2a.complete`，返回 `body.result.content`。镜像 twinkle `tests/test_agentserver_handler.py` 的连接范式。 | `websockets` |
| `scorer.py` | GAIA 风格归一化 + 匹配。**注：官方 scorer 未拉到，本版为合理近似，接真数据时对齐。** | stdlib |
| `run_gaia.py` | CLI 主入口：加载 → 逐题跑 → 打分 → 写报告。 | 上述 + stdlib |
| `samples/mini_gaia.jsonl` | ~6 条样本，混合 web_search 类 + 文件附件类。 | — |
| `samples/attachments/` | 文件类任务的小附件（tiny csv / txt，文本格式，避开 binary 坑）。 | — |
| `output/<timestamp>/` | 每题结果 JSON + 汇总。 | — |

## 6. 接口契约（与 twinkle 对接，已核对源码）

发送（WS → `ws://127.0.0.1:18000`）：
```json
{"protocol_version":"1.0","request_id":"<uuid>","channel":"web","session_id":"<per-task>","method":"chat.send","params":{"query":"<问题+指令>"},"timestamp":0.0}
```

接收：流式帧。
- 连上后先 `recv` 吃掉 `connection.ack`。
- `response_kind="e2a.chunk"` → 增量文本（`body.result.content`）。
- `response_kind="e2a.complete"` 且 `is_final=true` → 最终答案。
- `response_kind="e2a.error"` → 失败。

依据：`twinkle/agentserver/server.py`（`ws_handler` 路由非 RPC envelope 到 `run_stream`）、`agent_loop.py`（`run_stream` 读 `params.query`，final 发 `e2a.complete`，`body.result.content`）、`tests/test_agentserver_handler.py`（WS 客户端范式：`connect` → `recv` ack → `send(envelope.model_dump_json())` → 读帧）。

## 7. 样本 schema

```json
{"task_id":"s1","level":1,"question":"...","ground_truth":"Paris","attachment":"capitals.csv","hint":"..."}
```
- `attachment`：`null` 或 `samples/attachments/` 下文件名。runner 把它拷进 twinkle workspace，query 里告知文件名。
- `level`：1/2/3，仅用于报告分组，首版样本集中在前两级。

## 8. 附件处理

- harness 把附件拷到 twinkle workspace 目录（`TWINKLE_WORKSPACE_DIR` 或默认 `~/.twinkle`），让 agent 用 `read_file` / `command_exec` 访问。
- 文件始终在 workspace，不经 WS（WS = 文本 / 控制面，workspace 文件系统 = 数据面，分离）。
- 首版样本只用文本格式附件，避开 twinkle `read_file` 拒绝 binary（`_BINARY_EXTS`）的已知坑，先把管道跑通。

## 9. 答案抽取（basic）

- query 末尾追加：`\n\n只输出最终答案，不要解释。`
- 取 `e2a.complete` 的 `body.result.content`，strip；多行取最后一非空行（启发式）。
- 不做额外 LLM 抽取（后续改进）。

## 10. 打分归一化（GAIA 近似）

- 小写；去前导冠词（a / an / the）；去标点；压空白；数字归一（`1,000` → `1000`，`1.0` → `1`）。
- 判对规则：归一后预测 **等于** 金标，**或** 金标为预测的子串。
- **已知瑕疵**：子串匹配有误判风险（金标 `"1"` 会匹配预测 `"100"`）。首版接受，**接真数据时按官方 scorer 对齐**（官方会做更严格的边界 / 列表匹配）。
- 官方 scorer 未能拉到（HF gated + 本机网络封 HF），本版为合理近似。

## 11. CLI

```
python run_gaia.py --agentserver-url ws://127.0.0.1:18000 \
                   --workspace-dir ~/.twinkle \
                   --samples samples/mini_gaia.jsonl \
                   --per-task-timeout 300
```
默认值：`agentserver-url=ws://127.0.0.1:18000`、`workspace-dir=TWINKLE_WORKSPACE_DIR` 环境变量或 `~/.twinkle`、`output=output/<timestamp>/`。

## 12. 错误处理

- `e2a.error` → 该题判失败（记原因），计入总数但不计命中。
- 单题超时（`--per-task-timeout`）→ 失败。
- 连不上 AgentServer → 快速报错并退出："twinkle AgentServer 是否在运行？默认 :18000"。

## 13. 测试

- `scorer.py` 单测：覆盖各类归一（数字、冠词、标点、大小写、子串）与边界（空预测、超长预测）。
- 端到端冒烟：文档化——需 twinkle AgentServer 跑着 + `.env` 配好 `TWINKLE_LLM_API_KEY`；对样本集跑一遍，核对 `output/` 汇总。

## 14. 先决条件

- 设计 / spec / 造样本不需要 Bash / twinkle 运行。
- 端到端冒烟需：twinkle AgentServer 起在 :18000；`.env` 有 `TWINKLE_LLM_API_KEY`；workspace 目录可写。
- 运行环境：twinkle venv python（含 `websockets`）或任何装了 `websockets` 的 python。

## 15. 验收标准（可验证）

1. `python run_gaia.py --samples samples/mini_gaia.jsonl` 对着活的 twinkle AgentServer 跑完，打印并写出准确率汇总到 `output/<timestamp>/`。
2. `scorer` 单测全过。
3. 至少 1 条文件附件任务端到端跑通（文件落下 → agent 读到 → 答案被打分）。

## 16. 后续（接真 GAIA 时）

- 换 loader 读真实 GAIA validation（需 HF token + 授权 + 网络 / 镜像）。
- 对齐官方 scorer（替换 §10 的近似实现）。
- 加 LLM 答案抽取（agent 啰嗦输出 → 短答案）。
- 处理 binary 附件（接 `command_exec` 跑 `pypdf` / `openpyxl` 等解析库）。
- 并发跑（每题独立 `session_id`，twinkle `ws_handler` 每会话单任务，天然可并行）。
- 榜单提交格式。
