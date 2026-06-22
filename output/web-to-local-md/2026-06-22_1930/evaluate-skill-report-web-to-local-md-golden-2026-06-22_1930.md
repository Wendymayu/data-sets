# web-to-local-md 综合评估报告（批量模式）

**评估日期**: 2026-06-22_1930
**Skill 名称**: web-to-local-md
**黄金数据集**: D:\code\opensource\github\data-sets\skills\web-to-local-md\v1
**用例数量**: 7
**评估模式**: 批量评估（--golden 回归对比）

---

## 总览

| 指标 | 值 |
|------|-----|
| 测试用例数 | 7 |
| 结构通过率 | 97.96%（48/49 项通过） |
| 语义平均分 | 4.21/5 |
| 综合评分 | 88.4% |
| 总体评级 | ⭐⭐⭐⭐ |
| 评估结论 | **通过** |

**综合评分公式**：结构通过率×0.3 + 语义平均分换算百分比×0.7 = 97.96%×0.3 + 84.29%×0.7 = 29.39 + 58.99 = **88.39%**

**执行方式说明**：`--golden` 模式实际执行了目标 skill（按 web-to-local-md 的 SKILL.md「Implementation」章节运行核心脚本 `web_to_local_md.py`，该脚本 "handles all steps automatically"）。7 个用例并行执行，所有新生成文件写入项目本地 `output/web-to-local-md/2026-06-22_1930/case-{N}/`，未污染黄金数据集目录。策略分布：case-1~5、7 走 Strategy B（HTML 转换 → `index.md`），case-6 走 Strategy A（GitHub 源文件 → 嵌套 `ai/interview-questions/llm-interview-questions.md`）。7 个站点全部下载成功，图片下载 0 失败（共 82 张：5/4/13/23/10/1/26）。

**可复现性对比**：本运行综合评分 88.4%（⭐⭐⭐⭐ 通过），与上一运行（2026-06-22_1720，87.9%）基本一致，差异落在 evaluate-skill 文档所述 "LLM-as-Judge ±1 波动" 范围内。两轮运行的共性问题（图片 alt 退化 5/7、代码块语言标注丢失、冗余图片下载）与 case-6 的 IDENTICAL 完美匹配均稳定复现，验证评估结论的可复现性。

---

## 逐用例评分

| 用例 | 来源 | 策略 | 结构 | 完整性 | 准确性 | 合规性 | 可用性 | 语义均分 | 回归 | 关键问题 |
|------|------|------|------|--------|--------|--------|--------|---------|------|---------|
| case-1 | Anthropic 工程博客 | B | 7/7 | 5 | 5 | 5 | 5 | 5.00 | 进1 退1 | 2 个代码块缺 ```yaml 语言标注；图片用 hash 文件名（参考用语义化 `anthropic-evals-N.png`） |
| case-2 | 阿里云文档 | B | **6/7** | 4 | 5 | 3 | 3 | 3.75 | 退8 | 🔴 2 张表格分隔行在表头前 + 列数不一致；4 图 alt="image"；日期 2025-02-11≠参考 2024-11-20 |
| case-3 | 美团技术团队 | B | 7/7 | 5 | 4 | 3 | 4 | 4.00 | 进1 退3 | 8/9 图 alt="image"；日期下多 2 行元数据；4 张未引用冗余图 |
| case-4 | InfoQ 中文 | B | 7/7 | 5 | 5 | 4 | 4 | 4.50 | 退1 | 22 处图 alt 全为 "image" |
| case-5 | 掘金 | B | 7/7 | 5 | 4 | 2 | 3 | 3.50 | 退4 | 作者元数据未清理；文末推广块未移除；alt=hash 文件名；文件名冗长(~120字符) |
| case-6 | JavaGuide（VuePress） | A | 7/7 | 5 | 5 | 5 | 5 | 5.00 | 全不变 | 无——与黄金参考逐字符完全一致（diff IDENTICAL） |
| case-7 | AWS 中国博客 | B | 7/7 | 4 | 4 | 3 | 4 | 3.75 | 进1 退4 | 25 代码块缺语言标注；9 张作者头像冗余；alt=文件名英文；空 "## 本篇作者" 标题残留 |

---

## 逐用例详细评估

### case-1 — Anthropic 工程博客（Strategy B，en，medium）

**结构断言**：7/7 通过（100%）。文件 43769 字符，H1 + 多段落，5 张图均为本地 `images/` 路径，4 个表格行列对齐、2 个代码块围栏闭合（106/136、150/180）。

**合规性依据**：
- 完整性 5：H1、发布日期 `<small style="color:gray">2026-01-09</small>`（H1 下方）、Introduction 至 Appendix 全章节、5 图引用、2 个 YAML 代码示例、4 个表格完整。
- 准确性 5：正文与参考逐字一致无篡改；H1 句首大写 `Demystifying evals for AI agents` 贴合原博客实际标题；图 4 alt 修正了参考中错误的 "Grader types comparison" 为与图注一致的 "The process of creating an effective evaluation."（改进）。
- 合规性 5：12 条常见错误规则全部通过——日期 small 标签在 H1 下方、根目录 `images/xxx.png` 路径、无 Copy 残留、alt 由 `enrich_image_alts` 从 figcaption 填充。
- 可用性 5：Typora/VS Code 可离线阅读，标题层级清晰可导航，alt 具描述性利于无障碍。

**回归对比**：改进 1（图 4 alt 文本修正）、退化 1（2 个 YAML 代码块丢失 ```yaml 标注变为裸 ```）、不变 3（H1 大小写均 acceptable、图片文件名 hash vs 语义命名均有效、Claude.ai 重定向 UUID 会话级差异）。

---

### case-2 — 阿里云文档（Strategy B，zh，medium）

**结构断言**：6/7 通过（85.7%）。🔴 断言 7 失败：**两张表格的 `|---|` 分隔行出现在表头行之前**（line 19 在 line 20 前、line 52 在 line 53 前），且第二张表表头为 4 列但 Android/iOS、ACK Ingress、ALB、ASM、API Gateway、.NET/Node.js 等多行仅 3 列（丢失尾部空单元格），导致表格在主流渲染器无法正确渲染。

**合规性依据**：
- 完整性 4：H1、引言、3 级标题、2 表格全部数据行、4 图引用齐全；但 2 处表格分隔行位置错误致表格无法正常渲染，结构化数据可读性受损。
- 准确性 5：正文内容与黄金参考完全一致无事实错误；日期 2025-02-11（参考为 2024-11-20），疑为页面更新所致非提取错误。
- 合规性 3：表格分隔行置于表头前违反 Markdown 表格语法（SKILL.md Common Mistakes: regex 转换导致 lost tables）；4 图 alt 均为泛化 `image`，未按 `enrich_image_alts()` 从 figcaption/title 提取描述性 alt。
- 可用性 3：表格无法正常渲染，结构化数据以纯文本管道符展示；alt 泛化降低可访问性。

**回归对比**：退化 8（4 图 alt 退化、表格 1 分隔行位置、表格 2 分隔行位置、表格 2 列数、日期变化），不变 20。

---

### case-3 — 美团技术团队（Strategy B，zh，medium）

**结构断言**：7/7 通过（100%）。文件约 9KB，H1/H2/H3/列表/表格/blockquote/图片引用结构完整无破损，9 处图片引用均为本地 `images/<hash>.<ext>` 路径。

**合规性依据**：
- 完整性 5：正文文本、全部标题、五步表格、列表、blockquote、9 张引用图片完整呈现，与参考逐段一致。
- 准确性 4：正文文本与参考逐字一致；但 8 张正文图片 alt 退化为通用 `image`，未准确描述图片内容（参考有 "重构时间线与执行路径""AI 辅助技术债梳理流程""Pre-PR 与 AI CR 审查流程" 等描述性中文 alt）。
- 合规性 3：日期格式/H1 注入/图片本地路径/锚点链接清理均合规；**但 `<small>` 日期下多出 "业务研发平台 2026-05-07"（团队/栏目）和 "算法大模型"（标签）两行**，违反 SKILL.md "Only add the date — no author, category, or other metadata" 规则；images/ 目录有 4 张未引用图片属未清理噪声。
- 可用性 4：文档结构清晰可离线阅读，表格与行动指南完整；alt 退化和冗余图片略降目录整洁度。

**图片数差异（13 vs 9）已查清**：md 实际引用的 9 张内容图与参考 hash 文件名完全一致；多出的 4 个文件（`6c1215addf...jpg`、`01fab90c3e...png`、`0c57a460...png`、`ad51e26e...jpg`）未被 md 引用，系页面头像/推广图被下载但未嵌入正文——**目录冗余，非内容退化**。

**回归对比**：改进 1（锚点链接清理——参考 H2/H3/H4 为 `## [标题](#锚点)` 带锚点，新输出已清理为纯 `## 标题`，符合 `clean_html_artifacts()`）、退化 3（8 图 alt="image"、日期下多余 2 行元数据、4 张未引用冗余文件）、不变 8（frontmatter/H1/日期/9 图 hash 文件名/正文文本）。

---

### case-4 — InfoQ 中文（Strategy B，zh，hard）

**结构断言**：7/7 通过（100%）。文件 23124 字符，H1 + 有序列表 + PromQL 代码块（行 105-107 围栏闭合）正确，22 处图引用均本地 `images/` 路径。

**合规性依据**：
- 完整性 5：H1、日期 2024-07-24、完整正文、22 图引用、PromQL 代码块、有序列表均完整，信息量与参考一致。
- 准确性 5：正文文本与参考逐字一致，PromQL 示例（`topk(10, sum(rate(...)) by (app))`）正确，日期与 H1 准确。
- 合规性 4：本地图片路径、H1+small 日期注入、代码块围栏、无 Copy 残留均合规；扣分在 **22 处图 alt 全为 "image"**——`enrich_image_alts()` 应优先从 figcaption/title 提取描述性 alt（参考已实现 "演讲者介绍""异常检测算法分类""ARMS Insights 自动根因定位" 等），新输出 enrichment 步骤未生效，仅触发 fallback。
- 可用性 4：可离线阅读，图片正常显示；但 22 处 alt 全为 "image" 缺少上下文描述，可读性与无障碍性下降。

**回归对比**：退化 1（22 处 alt 退化），其余（H1/日期/正文/PromQL 代码块/图文件名/frontmatter）全不变。两份输出 images 文件夹均含未引用的 orphan 图 `ade7e79f...png`（23 文件/22 引用），为一致行为非新输出问题。

---

### case-5 — 掘金（Strategy B，zh，hard，.awebp）

**结构断言**：7/7 通过（100%）。文件约 3500+ 字符（121 行），H1/图片/列表/引用/HR 语法有效可解析，10 张图均 `images/` 本地路径，byteimg `.awebp` 文件名中 `:` 已正确 sanitize 为 `-`（`v1:0:0:0:0` → `v1-0-0-0-0`）。

**合规性依据**：
- 完整性 5：文章正文全部段落、JetBrains 停服时间表列表、10 张图片均完整捕获，无正文内容缺失。
- 准确性 4：正文文本与源页一致，图片正确下载；扣分在图片 alt 为 hash 文件名（如 `8f35ba86a0c6406aa1973cdb9f7383a4~tplv 73owjymdk6...`）非描述性文本。
- 合规性 2：**3 处违反 SKILL.md Common Mistakes**：1) 作者元数据未清理（CodeSheep 署名链接、重复日期 2026-03-30、阅读量 19,835、阅读时长"阅读6分钟"4 行噪声），违反 `extract_page_metadata` "Only add the date"；2) 文末 GitHub 仓库 "编程之路" 推广引用块未移除，违反 `clean_html_artifacts` promo blocks 清理；3) hash 图片 alt 未按 `fill_image_alt_text` "returns generic image for hash-dominated names" 返回通用 `image`，而返回完整 hash 文件名。
- 可用性 3：可离线阅读；但文件名冗长（~120 字符 CDN hash 名）、alt 无意义、头部散落 4 行噪声元数据、文末推广块未清理，整体阅读体验显著低于参考。

**回归对比**：退化 4（作者元数据保留、图片文件名冗长 hash、alt=hash 文件名、文末推广块未移除），不变 7（H1/日期行/正文段落/JetBrains 停服时间表/加粗/HR/图片数量）。

---

### case-6 — JavaGuide AI 面试题（Strategy A，zh，easy）⭐ 最佳

**结构断言**：7/7 通过（100%）。文件 12331 字符、173 行，1 个 H1 + 8 个 H2 + 表格/列表/代码块结构完整。**新输出与黄金参考逐字符完全一致（diff IDENTICAL，12331 字节均等），图片文件逐字节相同。**

**合规性依据**：
- 完整性 5：全 7 节（LLM 运行机制/API 调用工程/结构化输出与工具调用/AI 应用评测/答题框架/常见扣分点/复习建议）+ 考察表 + 8 道高频题清单完整，与黄金逐字符一致。
- 准确性 5：diff IDENTICAL；Token/上下文窗口/采样参数/幂等/限流/MCP/LLM-as-Judge 等技术表述准确无错。
- 合规性 5：Strategy A GitHub 源优先 ✓；嵌套两级 `ai/interview-questions/` 正确使用 `../../images/llm-token-process.png`（L60，本用例重点）✓；日期 small 标签在 H1 下方（L3，非上方）✓；frontmatter 已剥离 ✓；图片 alt "Token 化过程示例" 已填充非空。
- 可用性 5：Markdown 结构清晰可渲染，图片本地相对路径正确（1/1），Typora 可离线阅读，锚点链接 `../llm-basis/*.md` 保留。

**回归对比**：全部维度均为**不变**。**本用例无任何退化**——Strategy A 路径质量最高，验证了 SKILL.md「GitHub source markdown > HTML conversion」的核心原则。两轮运行均 IDENTICAL，确认 Strategy A 的确定性。

---

### case-7 — AWS 中国博客（Strategy B，zh，hard）

**结构断言**：7/7 通过（100%）。文件 52110 字符、701 行，25 个代码块（50 个围栏标记：38 列首 + 12 缩进）全部成对闭合，17 图引用均本地 `images/*.png` 路径。

**合规性依据**：
- 完整性 4：四大章节（范式/架构/部署/总结）、25 代码块、17 张架构图、6 个 MCP Server 配置、4 段核心代码解读完整；新增图 1-17 独立图注行（匹配源博客）。扣分在文末残留空 "## 本篇作者" 标题无作者内容、9 张作者头像已下载但 markdown 无引用，作者板块处理不彻底。
- 准确性 4：正文与 25 代码块逐一对照无事实错误、无截断、无乱码；图 1-17 图注与图片准确匹配。扣分在 17 图 alt 均为文件名衍生英文（如 `Practical guide to building agentic ai applications for aws china region1 1024x528`），未描述图片实际内容。
- 合规性 3：合规项——图片本地路径、H1+small 日期注入、17 张架构图从 WordPress 画廊正确展开为独立引用、正文噪声剥离。违规项——1) `enrich_image_alts()` 未生效，17 张 alt 未从 figcaption 富化为中文 "图 N 描述"，全部回退文件名英文；2) 全部 25 代码块丢失语言标注，全为裸 ```（参考正确标注 ```bash/```json/```python）；3) 作者板块噪声剥离不彻底——残留空标题 + 下载 9 张未引用作者头像。
- 可用性 4：文档结构完整、本地图片可加载、离线阅读体验良好；图注独立成行提升可读性。轻微减分：代码块无语言标注致无语法高亮、alt 为文件名英文降低可访问性、9 张孤儿头像造成目录冗余。

**图片数差异（26 vs 17）已查清**：md 引用的 17 张架构图与参考一致；多出的 9 张（`hcihang.jpg`/`awsdawei.jpg`/`chenyip.jpg`/`chuanxie.jpg`/`guoren.jpg`/`mlil.jpg`/`sijie.jpg`/`sunhua.jpg`/`tangaws.jpg`）均为作者头像，grep 确认 markdown 中零引用——**目录冗余，非内容退化**。

**回归对比**：改进 1（新增 17 个显式图注独立行）、退化 4（25 代码块语言标注丢失、17 图 alt=文件名英文、9 张作者头像冗余、空 "## 本篇作者" 标题残留）、不变 2（博客来源头省略属噪声剥离、列表标记 `*` vs `-` 均合法）。

---

## 共性问题（出现在 ≥3 个用例中）

### 1. 图片 alt 文本退化为通用/无意义文本（出现在 5/7 用例：case-2/3/4/5/7）⚠️ 最主要问题

- case-2：4 图 alt 全为 `image`
- case-3：9 图中 8 图 alt 为 `image`
- case-4：22 图 alt 全为 `image`
- case-5：alt 为原始 hash 文件名（冒号转空格）
- case-7：alt 为文件名衍生英文（如 `Practical guide to building agentic ai applications...`）

参考文件均提供描述性中文 alt（"阿里云端到端链路追踪架构图""异常检测算法分类""重构时间线与执行路径"等）。仅 case-1（英文，alt 由 figcaption 填充尚可）和 case-6（Strategy A 源文件自带）未受影响。这是当前 skill 输出与黄金参考最大的系统性差距，**两轮运行均稳定复现**。

### 2. 次要共性问题（各 2/7 用例，未达 ≥3 阈值但值得记录）

- **代码块语言标签丢失**（case-1 的 2 个 ```yaml、case-7 的 25 个 ```bash/json/python）：markdownify 转换时未保留 `<pre><code class="language-xxx">` 的语言 class，致裸 ``` 围栏无语法高亮。
- **images 目录冗余文件**（case-3 多 4 张、case-7 多 9 张作者头像）：图片下载阶段未过滤非正文图片，无关头像/推广图被下载到本地但未嵌入 md。

### 3. 单点严重问题

- **case-2 表格语法损坏**（仅此 1 例，但属 🔴 Critical 级断言失败）：markdownify 表格转换时分隔行与表头顺序倒置 + 列数不一致，致 2 张表格无法渲染。

### 4. 本轮新发现的次要问题

- **case-3 日期下多余元数据**：`<small>` 日期下方插入 "业务研发平台 2026-05-07"（团队/栏目）和 "算法大模型"（标签）两行，违反 date-only 规则。
- **case-5 作者元数据 + 推广块残留**：合规性仅得 2 分（7 用例最低），3 处 Common Mistakes 违规。
- **case-7 空 "## 本篇作者" 标题残留**：作者板块噪声剥离不彻底，参考完全去除该板块。

---

## 改进建议

> 建议均指向 SKILL.md 的具体位置，便于迭代优化。

### 建议 1（针对共性问题 1，最高优先级）——强化图片 alt 生成

**建议在 SKILL.md 的「Common Mistakes」表格中扩展 "Empty image alt text" 规则**：
- 当前规则仅要求 `enrich_image_alts()` 用 figcaption/title 填充、`fill_image_alt_text()` 对 hash 名返回 `image`。建议补充：**对中文站点（InfoQ/美团/掘金/AWS），alt 应优先从 `<figcaption>`/`title`/`alt` 属性提取描述性中文文本；当这些来源为空时，不应回退到通用 `image` 或 hash 文件名，而应保留原文 `<figcaption>` 文本或基于图片周围段落生成简短描述**。这是当前 5/7 用例退化的根因，两轮运行均复现。

### 建议 2（针对共性问题 2a）——保留代码块语言标注

**建议在 SKILL.md 的「Common Mistakes」表格新增一行**：
- 规则名：`代码块语言标签丢失`；现象：`<pre><code class="language-yaml">` 转换后变为裸 ``` 围栏，无语法高亮；修复：`clean_html_artifacts()` 或 markdownify 转换前，提取 `<code>` 的 `language-*` class，注入为围栏语言标注（```yaml/```bash/```python）。影响 case-1（2 块）、case-7（25 块）。

### 建议 3（针对共性问题 2b）——过滤非正文图片

**建议在 SKILL.md 的「Implementation」步骤 4（Download images）中补充过滤规则**：
- 当前 `all_remote_images` 收集了页面所有 `<img>`，包括作者头像、推广图。建议：**仅下载正文内容区（`<article>`/`<main>`/`figure`）内、且被 md 实际引用的图片；对作者头像（常见于 `<figure class="author-avatar">` 或 `.jpg` 姓名型文件名）、推广 banner 在下载阶段过滤**。可消除 case-3（4 张）、case-7（9 张）的目录冗余。

### 建议 4（针对 case-2 单点问题）——修复表格转换语法

**建议在 SKILL.md 的「Common Mistakes」表格新增一行**：
- 规则名：`Markdown 表格分隔行/表头顺序倒置`；现象：markdownify 转换 HTML `<table>` 时 `|---|` 分隔行出现在表头行之前，且部分行列数不足致渲染错乱；修复：`convert_image_tables()`/表格转换逻辑需保证 **表头行在前、分隔行紧随其后、各数据行列数与表头一致（不足补空单元格）**。影响 case-2（2 张表，唯一的 Critical 断言失败）。

### 建议 5（针对 case-5 + case-3 + case-7）——清理推广/元数据内容

**建议在 SKILL.md 的「Common Mistakes」表格新增一行**：
- 规则名：`推广引用块与作者元数据残留`；现象：文末 GitHub 仓库推广引用块（case-5）、作者署名/阅读量/阅读时长元数据（case-5）、`<small>` 日期下的团队栏目/标签行（case-3）、空 "## 本篇作者" 标题（case-7）未被 `clean_html_artifacts()` 清理；修复：在 `NOISE_CLASSES`/噪声选择器中增加推广引用块（`.promotion`/文末 CTA）、作者元数据块、空作者板块的识别与剥离；`extract_page_metadata` 强化 "仅保留日期" 规则，剔除紧邻日期的团队/栏目/标签文本。

---

## 结论

**总体评级 ⭐⭐⭐⭐（综合 88.4%，通过）**。web-to-local-md 在 7 个黄金用例上整体表现优质：

- ✅ **核心转换质量稳定**：7/7 用例结构断言几乎全过（48/49），H1/日期/图片本地化/路径规则/WordPress 表格展开等硬规则均正确执行，全部图片下载 0 失败。
- ✅ **Strategy A 路径完美且确定**：case-6 与黄金参考逐字符一致（diff IDENTICAL），两轮运行均复现，验证了 "GitHub source > HTML conversion" 的核心原则。
- ⚠️ **主要短板是图片 alt 质量**（5/7 用例退化）——这是当前与黄金参考最大的系统性差距，建议优先按建议 1 优化 `enrich_image_alts()`/`fill_image_alt_text()` 对中文站点的处理。
- ⚠️ **代码块语言标签丢失**（case-1/7）和**冗余图片下载**（case-3/7）是次要但明确的退化点，两轮均稳定复现。
- 🔴 **case-2 表格语法损坏**是唯一的 Critical 级断言失败，需按建议 4 修复表格转换逻辑。
- 📊 **可复现性确认**：本运行（88.4%）与上一运行（87.9%）结论一致（均 ⭐⭐⭐⭐ 通过），共性问题与 case-6 完美匹配稳定复现，差异在 LLM-as-Judge ±1 波动范围内。

整体而言 skill 可直接用于离线阅读场景，但若要追平黄金参考的描述性 alt 与代码高亮质量，需按上述 5 条建议迭代 SKILL.md 与脚本。

---

*综合评估报告由 evaluate-skill skill 自动生成。核心定位：skill 质量改进的反馈工具，不是绝对质量裁判。*
