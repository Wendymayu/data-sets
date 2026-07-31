# GAIA → Twinkle 评测 Harness

驱动 twinkle agent 答 GAIA 题，归一化精确匹配打分，产出准确率报告（含 `summary.md` + 低分原因分析）。
设计 spec：`docs/superpowers/specs/2026-07-30-gaia-twinkle-harness-design.md`。

## 数据布局

```
gaia_twinkle/data/
  gaia/          # raw gated GAIA 数据集（gitignore，本地）—— 从 HF 下载后放这
  easy/          # GAIA L1 无附件（易）—— convert_gaia 生成，gitignore
  medium/        # GAIA L2 无附件（中）—— convert_gaia 生成，gitignore
  hard/          # GAIA L3 无附件（难）—— convert_gaia 生成，gitignore
  attachments/   # GAIA 带附件题（任意 level，测文件路径）—— convert_gaia 生成，gitignore
  smoke/         # 冒烟集：6 条手造假样本（committed，无需 gated 数据）
```
> GAIA 是 HF gated 数据（license：不得在可抓取格式下再分发）。raw parquet 与派生 jsonl 均 gitignore、不提交。
> `smoke/` 是自造假样本，license-safe，可提交。
> 难度对应：easy=L1、medium=L2、hard=L3（GAIA 的 Level 字段）。

## 前置

1. twinkle AgentServer 跑在 `ws://127.0.0.1:18000`（`python -m twinkle.agentserver`）。
2. twinkle `.env` 配好 `TWINKLE_LLM_API_KEY`。
3. harness 用独立 venv（不依赖 twinkle 的 venv）——首次安装：
   ```bash
   cd D:/code/opensource/github/data-sets
   python -m venv .venv                                       # Python 3.11+；或 D:/env/python/python.exe
   .venv/Scripts/python.exe -m pip install -r gaia_twinkle/requirements.txt
   ```
   之后所有 `python -m ...` 命令在 `data-sets\` 根、`.venv` 激活后运行（或直接用 `.venv\Scripts\python.exe`）。

## 跑测试

```bash
python -m pytest gaia_twinkle/tests -v
```

## 生成 GAIA eval 集（首次 / 数据更新时 / 换机器）

GAIA raw + 派生集都 gitignore、不进 git。新机器从零搭 `data/`（`smoke/` 已 committed，无需下载）：

1. HF token + GAIA 访问（浏览器，一次性）：
   - https://huggingface.co/settings/tokens → New token (Read) → `hf_xxx`
   - https://huggingface.co/datasets/gaia-benchmark/GAIA → Request access（auto 秒批）

2. 下载 GAIA raw 到 `gaia_twinkle/data/gaia/`（用仓库根的 `download_hf_dataset.py`，stdlib+curl，绕 Windows+镜像坑）：
   ```bash
   python download_hf_dataset.py gaia-benchmark/GAIA --token hf_xxx --out gaia_twinkle/data/gaia
   # 默认走 hf-mirror.com（国内）；能直连 HF 加 --mirror https://huggingface.co
   # 重跑跳过已下完文件；再跑一次应得 ok=0 skipped=N failed=0 即完整
   ```

3. 生成派生 eval 集（从 raw parquet 抽）：
   ```bash
   python -m gaia_twinkle.convert_gaia --preset easy         # L1 无附件 -> 42
   python -m gaia_twinkle.convert_gaia --preset medium       # L2 无附件 -> 66
   python -m gaia_twinkle.convert_gaia --preset hard         # L3 无附件 -> 19
   python -m gaia_twinkle.convert_gaia --preset attachments  # 任意 level 带附件 -> 38
   # 或手动: --parquet <path> --out <path> --level N --no-attachment|--with-attachment --limit M
   ```

> token 别外泄：`--token` 传或 `$HF_TOKEN`；`./.hf_token` 文件已 gitignore，别提交。raw + 派生集都不进 git。

## 跑评测

```bash
python -m gaia_twinkle.run_gaia --eval-set smoke              # 冒烟（6 假样本，无需 GAIA）
python -m gaia_twinkle.run_gaia --eval-set easy --limit 10   # L1 无附件，截 10 题快跑
python -m gaia_twinkle.run_gaia --eval-set medium            # L2 无附件
python -m gaia_twinkle.run_gaia --eval-set hard              # L3 无附件（最难）
python -m gaia_twinkle.run_gaia --eval-set attachments       # 带附件题（测文件路径）
# 自定义: --samples <path> --attachments-dir <path> --per-task-timeout 180 --limit N
```

结果写到 `gaia_twinkle/output/<timestamp>/`：`results.jsonl` + `summary.json` + `summary.txt` + `summary.md`
（含准确率 / 逐题表 / 失败模式分布；`accuracy<50%` 时附"得分过低原因分析"）。

> 注意：`attachments` 集里大量附件是二进制（pdf/xlsx/png/mp3 等），twinkle 的 `read_file` 当前拒绝二进制
> —— 这类题会失败（已知 twinkle 能力缺口）。文本附件（csv/txt）能读。随 twinkle 补齐 binary 解析后，此集才有意义。

## 如何选择数据集

按目的选 `--eval-set`：

| 场景 | 命令 | 说明 |
|---|---|---|
| 冒烟（改完代码/重启 twinkle 后验链路） | `--eval-set smoke` | 6 假样本，无需 GAIA 数据，最快，确认 harness↔twinkle 连通 |
| 快速看 twinkle 基础能力 | `--eval-set easy --limit 10` | L1 无附件 10 题，纯推理为主，~1-2 分钟 |
| twinkle 当前能拿分的全集 | `--eval-set easy` | L1 无附件 42 题 |
| 中等难度（多步推理） | `--eval-set medium` | L2 无附件 66 题 |
| 压力测试 / 未来能力 | `--eval-set hard` | L3 无附件 19 题，gpt-4o-mini 当前基本拿不到 |
| 测文件路径 | `--eval-set attachments` | 38 题带附件（L1/L2/L3 混合，无难易区分）；多数二进制，twinkle 当前读不了 |

选型要点：
- **先 smoke 后真数据**：每次改 harness 或重启 twinkle，先 `--eval-set smoke` 确认 6/6 通，再跑真集——排除环境/连通问题。
- **`--limit N` 快跑**：初次试某集先 `--limit 10`，省时间 / API。
- **`--concurrency N`**：并发跑 N 题（默认 4），大幅提速；过高会撞 LLM 限流（429），按你的 API 额度调。结果仍按输入顺序写入报告。
- **`--per-task-timeout`**：纯推理题 60s 够；web 依赖题给 180s+（twinkle 的 `web_search` 慢 / 可能拿不到结果）。
- **难度递进**：easy → medium → hard。分数会逐级掉，符合预期（GAIA L3 对当前模型本就极难）。
- **`attachments` 单独看**：它混了 L1/L2/L3、难易不分，主要用来验"twinkle 能不能处理附件"这条能力轴；当前因 binary 缺口多数会失败，别拿它当主分数。
- **自定义**：`--samples <path> --attachments-dir <path>` 可跑任意 jsonl（如自己裁的子集），`--eval-set` 只是预设快捷方式。

> 当前两个 twinkle 侧瓶颈会压低所有真集分数：① `web_search`（DuckDuckGo HTML 被反爬）→ web 题超时空答；
> ② `read_file` 拒二进制 → attachments 里 pdf/xlsx/png/mp3 题失败。这俩修了之后 easy/medium/hard/attachments 的分才真有参考价值。

## 实测

2026-07-31，gpt-4o-mini，easy 集 10 题（60s/题）：3/10。纯推理题全过；web 依赖题超时——
根因是 twinkle 的 `web_search`（DuckDuckGo HTML）被反爬挡返回空结果，属 twinkle 侧待修，非 harness 问题。
