# GAIA→Twinkle 评测驱动的迭代 TODO（飞轮）

> 目标：让 `eval → 修 → 重跑` 成自循环飞轮。
> 现状：eval 这半边已成型（可复现指标 + 分级集 + 失败模式/低分原因分析），但还差几块才"自循环"，且**第一转是修 infra，不是堆数据**。

## 关键认知

- twinkle 接外部 LLM（gpt-4o-mini），**不是自训练模型** → 迭代对象是 agent 的**工具 / prompt / skill / 记忆**，不是模型权重。GAIA 是**固定燃料（评测集）**，非"生成新数据"的来源。
- 第一转瓶颈是 **infra**（`web_search` 拿不到结果 + binary 读不了），不是 model / data。这俩修了，eval 才开始真测推理。

## 待做

### P0 — 让 eval 测推理而非 infra（第一转，解锁分数）
- [ ] 修 twinkle `web_search`：DuckDuckGo HTML 端点被反爬（对 httpx 返回 202 + 无 `result__a` 链接 → 解析得空）→ 换可用后端（Bing / Google CSE / Searx / 付费 search API）。
- [ ] 加 binary 附件读取：twinkle `read_file` 当前拒二进制（`_BINARY_EXTS`：pdf/xlsx/png/mp3/docx…）。加 `read_attachment` 工具，或让 `command_exec` 装 `pypdf`/`openpyxl`/`Pillow`/`whisper` 解析后喂文本。
- [ ] 重跑 `--eval-set easy` 验证：分数应跳，web/attachment 类题解锁。

### P1 — 让迭代可视、防回归
- [ ] 加 `compare <runA> <runB>` 子命令：按 `task_id` 对齐两次 run 的 results.jsonl，列出**翻牌（错→对）/ 回归（对→错）**。否则迭代是盲的（看不出改 A 坏没坏 B）。
- [ ] golden 回归门：挑 `smoke` + N 道"twinkle 现在稳定做对的 easy 题"作必须恒绿门（CI/本地门禁用）。

### P2 — 让指标可信、信号干净
- [ ] 报告里**分开"infra 失败"与"推理失败"**：现在 `timeout`（web 拿不到结果）淹没推理信号，分数主要在测工具链而非推理。可加"有效推理分"（剔除 infra 失败再算）。
- [ ] 收紧 scorer **子串瑕疵**：归一后"金标为预测子串即判对"导致 `gold "2"` 匹配 `pred "42"` 这类假阳。改匹配规则（词边界 / 列表匹配），让指标不虚高。

### P3（可选）— 字面"数据飞轮"
- [ ] 若日后要攒数据 fine-tune 专属模型：harness 把失败 case 的 agent trace（工具调用 / 搜索结果 / 模型输出）落盘成训练素材。当前无此组件。

## 飞轮第一转顺序

1. 修 `web_search`（P0）
2. 加 binary 读取（P0）
3. 加 `compare` 子命令（P1）
4. 重跑 `easy` → 看分数跳 + 翻牌 → 飞轮转起来

## 现状基线（2026-07-31，gpt-4o-mini）

| eval-set | 结果 | 说明 |
|---|---|---|
| smoke | 6/6（100%） | 链路通 |
| easy（L1 无附件，10 题，60s/题） | 3/10（30%） | 纯推理全过；web 题超时（`web_search` 缺陷） |
| medium / hard / attachments | 待跑 | 等 `web_search`/binary 修后才有意义 |

> 已知 twinkle 侧两个瓶颈压低所有真集分数：① `web_search`（DDG 反爬）→ web 题超时空答；② `read_file` 拒二进制 → attachments 里 pdf/xlsx/png/mp3 题失败。修了之后 easy/medium/hard/attachments 的分才有参考价值。
