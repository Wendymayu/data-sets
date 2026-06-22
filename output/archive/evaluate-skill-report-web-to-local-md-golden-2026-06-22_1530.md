# web-to-local-md 综合评估报告（批量模式）

**评估日期**: 2026-06-22_1530
**Skill 名称**: web-to-local-md
**黄金数据集**: D:\code\opensource\github\data-sets\skills\web-to-local-md\v1
**用例数量**: 7

---

## 总览

| 指标 | 值 |
|------|-----|
| 测试用例数 | 7 |
| 结构通过率 | 87.8% |
| 语义平均分 | 3.29/5 |
| 综合评分 | 72.4% |
| 总体评级 | ⭐⭐⭐ |

**评估结论**: 通过（≥70%门槛）——但存在 2 个严重退化用例（case-5 掘金、case-7 AWS），需重点修复

---

## 逐用例评分

| 用例 | 结构 | 完整性 | 准确性 | 合规性 | 可用性 | 回归 | 关键问题 |
|------|------|--------|--------|--------|--------|------|---------|
| case-1 Anthropic | 7/7 ✅ | 5 | 4 | 3 | 4 | ⚠️退化 | 缺少发布日期 |
| case-2 阿里云 | 6/7 ⚠️ | 3 | 4 | 2 | 3 | ⚠️退化 | 内容仅3971字(参考7487字)、缺日期、表头错误 |
| case-3 美团 | 7/7 ✅ | 4 | 4 | 3 | 4 | ⚠️退化 | 缺发布日期，内容偏短 |
| case-4 InfoQ | 7/7 ✅ | 4 | 4 | 3 | 4 | ⚠️退化 | 缺发布日期，内容偏短 |
| case-5 掘金 | 5/7 ❌ | 2 | 3 | 1 | 2 | ⚠️严重退化 | 10张图片全CDN URL、0下载、`\*\*`格式损坏 |
| case-6 JavaGuide | 7/7 ✅ | 4 | 5 | 5 | 4 | —不变 | 最佳用例（Strategy A） |
| case-7 AWS | 6/7 ⚠️ | 2 | 3 | 1 | 2 | ⚠️严重退化 | 17张架构图全丢失、`|---|`占位符 |

---

## 逐用例结构断言详情

### case-1（Anthropic 工程博客 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 index.md + 5 images |
| 2 | 文件非空 | ✅ | 42488 chars |
| 3 | Markdown 可解析 | ✅ | 含多个 # 标题、段落、表格、代码块 |
| 4 | 无未填充占位符 | ✅ | 无 TODO/TBD/FIXME/{PLACEHOLDER} |
| 5 | 图片引用是本地路径 | ✅ | 5 张图片全部使用 `images/xxx.png` 本地路径 |
| 6 | 占位标记占比 <30% | ✅ | 0%，无[链接暂缺]等标记 |
| 7 | 无 Markdown 语法损坏 | ✅ | 表格行列对齐，代码块闭合 |

**通过率**: 7/7 (100%)

### case-2（阿里云端到端链路追踪 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 index.md + 4 images |
| 2 | 文件非空 | ✅ | 3971 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 4 张图片使用 `images/p87336x.png` 本地路径 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ❌ | 🟢 Low — 表格 `| --- | --- | --- | --- |` 作为首行出现，缺少正确表头行；分隔行在表头行之前，导致表格渲染异常 |

**通过率**: 6/7 (85.7%)

### case-3（美团技术团队 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 index.md + 9 images |
| 2 | 文件非空 | ✅ | 8207 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落、表格 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 9 张图片使用 `images/xxx.png` 本地路径 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 表格和代码块格式正常 |

**通过率**: 7/7 (100%)

### case-4（InfoQ 阿里云可观测 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 index.md + 23 images |
| 2 | 文件非空 | ✅ | 10436 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 23 张图片使用 `images/xxx.png` 本地路径 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 格式正常 |

**通过率**: 7/7 (100%)

### case-5（掘金 JetBrains — Strategy B，已知困难用例）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 index.md，但 0 images |
| 2 | 文件非空 | ✅ | 7728 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ❌ | 🟡 Medium — 全部 10 张图片仍使用 byteimg CDN `https://` 签名 URL，0 张下载到本地。违反 SKILL.md "图片引用是本地路径"规则 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ❌ | 🟢 Low — `\*\*第一点...\*\*` 使用转义星号而非 `**粗体**` 格式；图片 alt 文本包含乱码 URL 参数（如 `tplv 73owjymdk6 jj mark v1:0:0:0:0:5o6Y6YeR...`），违反 `fill_image_alt_text()` 规则 |

**通过率**: 5/7 (71.4%)

### case-6（JavaGuide AI 专栏 — Strategy A）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 ai/interview-questions/llm-interview-questions.md + 1 image |
| 2 | 文件非空 | ✅ | 5411 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落、表格 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 使用 `../../images/llm-token-process.png` 正确的子目录相对路径 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 格式正常 |

**通过率**: 7/7 (100%)

### case-7（AWS 中国区博客 — Strategy B，已知困难用例）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | 找到 index.md，但 0 images |
| 2 | 文件非空 | ✅ | 26325 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅* | 无 `![]()` 图片引用（17 张参考图片完全丢失，output 中 0 张图片存在） |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ❌ | 🟢 Low — 多处 `| --- |` 单独出现（原 WordPress `<table><td><figure><img>` 结构残留），无效 Markdown 表格标记 |

**通过率**: 6/7 (85.7%)，但 ⚠️ 严重质量缺陷：17 张架构图完全丢失

---

## 逐用例 SKILL.md 合规性评估

### case-1（Anthropic 工程博客）

**完整性 (5/5)**：输出包含完整文章内容（335 行，42488 chars），涵盖 Introduction → Eval structure → Why build evals → Types of graders → Agent types → Non-determinism → Roadmap → Conclusion → Appendix 所有板块。5 张图片本地下载。判断依据：index.md 包含全部 SKILL.md 要求的页面内容和图片下载。

**准确性 (4/5)**：内容事实准确，与 Anthropic 工程博客原文一致。无编造内容。判断依据：文章各板块内容可直接对照原网页验证，技术术语和引用均准确。扣 1 分：部分链接仍为外部 URL（如 `[Building effective agents](https://www.anthropic.com/...)`），这些链接指向外部站点而非本地文件。

**合规性 (3/5)**：Strategy B 正确选择（非开源站点）；图片下载并路径本地化 ✅；无 "Copy" 按钮残留 ✅。但违反 1 条规则：**缺少发布日期**——SKILL.md 明确要求"Add `<small style="color:gray">YYYY-MM-DD</small>` below the H1 title"，但 output 的 `# Demystifying evals for AI agents` 后无日期标记（参考有 `<small style="color:gray">2026-01-09</small>`）。判断依据：output line 1-3 无 `<small>` 标签，违反 `extract_page_metadata()` 规则。

**可用性 (4/5)**：内容在 Typora/VS Code 中可正常阅读，图片本地加载，表格和代码块渲染正常。缺少发布日期为小瑕疵，不影响主要内容阅读。

### case-2（阿里云端到端链路追踪）

**完整性 (3/5)**：输出内容仅 3971 chars（参考为 7487 chars），约 53% 的内容量。主要板块存在（解决方案概述、插桩方式、云产品接入、上下文透传），但部分段落内容偏薄。判断依据：脚本报告 "Strategy B OK: 3971 chars"，内容量明显低于参考的 7487 chars，阿里云文档的完整表格和部分段落可能未被完整提取。

**准确性 (4/5)**：提取的内容事实准确，技术术语正确。判断依据：链路追踪、ARMS、OpenTelemetry 等专业内容与原文一致。

**合规性 (2/5)**：违反 2 条规则：(1) 缺少发布日期（参考有 `<small style="color:gray">2024-11-20</small>`，output 无）；(2) 表格格式错误——`| --- | --- | --- | --- |` 作为首行而非表头行，违反 Markdown 表格规范。判断依据：output line 17 表格首行是分隔行而非表头行；output 缺 `<small>` 日期标记。

**可用性 (3/5)**：内容可阅读但偏短，表格渲染异常。图片本地加载正常。需要手动修正表格格式才能在 Typora 中正确显示。

### case-3（美团技术团队）

**完整性 (4/5)**：输出包含完整文章主体（背景、重构动因、时间线、SOP、总结），9 张图片本地下载。判断依据：所有主要板块均存在，但内容量（8207 chars）低于参考（20250 chars），可能丢失了部分次要段落或格式差异。

**准确性 (4/5)**：内容准确，无编造。判断依据：AI Coding 管理实践、技术债梳理、SOP 分发等内容与原文一致。

**合规性 (3/5)**：违反 1 条规则：缺少发布日期（output 无 `<small>` 标签）。H1 标题存在但图片在标题之前（line 1 是图片引用，line 3 才是 H1），违反 SKILL.md "inject as `# title` first line" 规则。判断依据：output line 1 `![...]` 图片引用在 H1 之前；output 无 `<small>` 日期。

**可用性 (4/5)**：内容可正常阅读，图片本地加载，表格格式正确。图片在标题前为小瑕疵。

### case-4（InfoQ 阿里云可观测）

**完整性 (4/5)**：输出包含完整演讲内容（异常检测、根因定位、PromQL/LLM），23 张图片本地下载。判断依据：内容量 10436 chars（参考 23693 chars），主要板块完整但部分内容偏短。

**准确性 (4/5)**：提取内容准确。判断依据：AIOps、异常检测算法、根因定位等技术内容与原文一致。

**合规性 (3/5)**：违反 1 条规则：缺少发布日期。判断依据：output 无 `<small>` 日期标记。图片路径本地化 ✅，无按钮残留 ✅。

**可用性 (4/5)**：内容可正常阅读，图片本地加载。内容偏短但不影响核心信息获取。

### case-5（掘金 JetBrains — ❌ 严重退化）

**完整性 (2/5)**：文本内容存在（7728 chars），但 0 张图片下载到本地——全部 10 张图片仍指向 byteimg CDN 签名 URL，无法离线阅读。判断依据：脚本报告 "Downloading 0 images"，output 中 10 处 `![...]()` 均为 `https://p3-xtjj-sign.byteimg.com/...` CDN URL。

**准确性 (3/5)**：文本内容基本准确，但图片无法验证（CDN 签名 URL 有过期时间，离线阅读时图片将失效）。判断依据：byteimg 签名 URL 包含 `x-expires=1782091415`，过期后图片不可访问。

**合规性 (1/5)**：违反 3+ 条 SKILL.md 规则：(1) 图片引用非本地路径——违反 "Download images + fix paths" 步骤；(2) `\*\*text\*\*` 转义粗体标记——违反 "Convert to Markdown with markdownify" 质量要求；(3) 图片 alt 文本包含乱码 URL 参数而非人类可读描述——违反 `fill_image_alt_text()` 规则。判断依据：output line 19-97 所有图片仍为 CDN URL；line 53 `\*\*第一点...\*\*` 格式错误；alt 文本如 `8f35ba86a0c6406aa1973cdb9f7383a4~tplv 73owjymdk6 jj mark v1:0:0:0:0:5o6Y6YeR...` 不可读。

**可用性 (2/5)**：无法用于离线阅读（图片全部 CDN URL 且有过期时间），粗体文本不渲染。勉强可阅读文字内容，但需要大量手动修正才能实际使用。

### case-6（JavaGuide AI 专栏 — ✅ 最佳用例）

**完整性 (4/5)**：Strategy A（GitHub 源）成功下载 md 文件，1 张图片本地下载，内容完整。判断依据：脚本报告 "Pages: 1 success"，下载了 `llm-interview-questions.md`（5411 chars），图片 `llm-token-process.png` 本地化。

**准确性 (5/5)**：GitHub 源 markdown 是最准确的来源（SKILL.md 明确指出 "GitHub source markdown > HTML conversion"）。判断依据：Strategy A 直接从 GitHub 仓库下载原始 .md 文件，内容与源仓库一致。

**合规性 (5/5)**：完全合规：(1) 发布日期正确添加 `<small style="color:gray">2026-05-18</small>` 在 H1 下方；(2) 图片使用子目录相对路径 `../../images/xxx.png`；(3) Strategy A 正确选择；(4) H1 标题作为首行。判断依据：output line 1-3 格式完全符合 SKILL.md 规则。

**可用性 (4/5)**：内容在 Typora 中可正常阅读，图片本地加载，表格格式正确。部分内部链接（如 `[《LLM 运行机制》](../llm-basis/...)`）为相对路径，可能需手动调整。

### case-7（AWS 中国区博客 — ❌ 严重退化）

**完整性 (2/5)**：文本内容大量（26325 chars），但 17 张架构图完全丢失。AWS 博客重度依赖图片展示架构，无图片的输出严重不完整。判断依据：脚本报告 "Downloading 0 images"，参考有 17 张架构图，output 中无任何 `![]()` 图片引用，图片位置变为 `| --- |` 或纯文本描述"图 X. ..."。

**准确性 (3/5)**：文本内容事实准确，但缺少 17 张关键架构图导致视觉信息完全丢失。判断依据：Strands Agents、DeepResearch 等架构描述缺少配套图片，读者无法理解架构布局。

**合规性 (1/5)**：违反多条规则：(1) 核心图片下载步骤完全失败——17 张图片 0 张下载，违反 "Download images + fix paths"；(2) 发布日期位置错误——`<small>` 在 H1 标题之前而非之后；(3) WordPress `<table><td><figure><img>` 嵌套结构提取为 `| --- |` 占位符而非图片引用。判断依据：output line 1 `<small>` 在 line 3 `# 标题` 之前；多处 `| --- |` 无效表格标记；0 张图片下载。

**可用性 (2/5)**：17 张架构图完全丢失使得博客内容难以理解（架构类文章高度依赖可视化）。`| --- |` 占位符在 Typora 中显示为空白表格行。勉强可阅读文字内容，但需要手动补充所有图片。

---

## 回归对比

### case-1（Anthropic）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ⚠️退化 | output 缺少 `<small style="color:gray">2026-01-09</small>` 发布日期 |
| 语义差异 | —不变 | 文章内容与参考一致，无信息偏误 |
| 格式差异 | ⚠️退化 | 图片文件名从人类可读名（`anthropic-evals-1.png`）变为 hash 名（`bd42e7b2f3e9bb5218142796d3ede4816588dec0-4584x2834.png`） |

### case-2（阿里云）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ⚠️退化 | output 缺发布日期；内容仅 3971 chars（参考 7487 chars，约 53%） |
| 语义差异 | ⚠️退化 | 多个段落和表格内容未完整提取，信息密度下降 |
| 格式差异 | ⚠️退化 | 表格 `| --- | --- | --- | --- |` 作为首行，参考有正确表头 |

### case-3（美团）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ⚠️退化 | output 缺发布日期；图片在 H1 之前 |
| 语义差异 | ⚠️退化 | 内容量 8207 chars vs 参考 20250 chars（约 40%），部分段落可能丢失 |
| 格式差异 | —不变 | Markdown 结构基本正常 |

### case-4（InfoQ）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ⚠️退化 | output 缺发布日期 |
| 语义差异 | ⚠️退化 | 内容量 10436 chars vs 参考 23693 chars（约 44%） |
| 格式差异 | —不变 | 格式基本正常 |

### case-5（掘金 — 严重退化）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ⚠️严重退化 | 参考 10 张 .awebp 图片本地下载，output 0 张下载（全 CDN URL） |
| 语义差异 | ⚠️严重退化 | 图片为 byteimg 签名 URL（含 `x-expires`），过期后内容不可用 |
| 格式差异 | ⚠️严重退化 | 参考 `**粗体**` → output `\*\*转义粗体\*\*`；参考 `![JetBrains品牌标识](images/xxx.awebp)` → output `![乱码URL参数](https://p3-xtjj-sign.byteimg.com/...)` |

### case-6（JavaGuide — 不变/改进）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ✅一致 | 发布日期位置正确，内容结构完整 |
| 语义差异 | —不变 | GitHub 源 markdown 内容准确 |
| 格式差异 | —不变 | 子目录相对路径正确 |

### case-7（AWS — 严重退化）

| 维度 | 对比结果 | 详情 |
|------|---------|------|
| 结构差异 | ⚠️严重退化 | 参考 17 张图片本地下载，output 0 张；日期在 H1 之前而非之后 |
| 语义差异 | ⚠️严重退化 | 17 张架构图全部丢失，视觉信息完全缺失 |
| 格式差异 | ⚠️严重退化 | 参考 `![架构图](images/xxx.png)` → output `| --- |` 无效占位符 |

---

## 共性问题（出现在 ≥3 个用例中）

### 1. 缺少发布日期标记（4 个用例：case-1, 2, 3, 4）

SKILL.md 明确要求在 H1 标题下方添加 `<small style="color:gray">YYYY-MM-DD</small>` 日期标记，由 `extract_page_metadata()` 函数处理。但 4 个 Strategy B 用例的输出均缺少此标记。case-6（Strategy A）正确添加了日期，说明 `extract_page_metadata()` 在 Strategy B 路径下可能未被正确调用或提取失败。

### 2. Strategy B 提取内容偏短（3 个用例：case-2, 3, 4）

阿里云文档（3971/7487 = 53%）、美团博客（8207/20250 = 40%）、InfoQ（10436/23693 = 44%）三个用例的 Strategy B 提取内容量显著低于参考。可能是 HTML 主内容区域选择器不够全面，部分内容在嵌套容器中未被提取。

---

## 改进建议

### 1. 修复发布日期提取（4 用例受影响）

建议在 SKILL.md 的步骤 3（Extract content）中补充明确要求：Strategy B 场景下，`extract_page_metadata()` 必须在噪声清理之前从 `<time>`、`<span class="date">`、`.post-date`、`.pubdate`、`meta[property="article:published_time"]` 等 HTML 元素提取发布日期，并在 H1 标题下方插入 `<small style="color:gray">YYYY-MM-DD</small>`。当前脚本在 Strategy B 单页提取路径下可能跳过了 `extract_page_metadata()` 调用——建议检查脚本 `strategy_b_single_page()` 函数是否正确调用了该函数。

### 2. 增强 Strategy B 内容提取选择器（3 用例受影响）

建议在 SKILL.md 的 Strategy B 步骤中补充说明：当 HTML 主内容区域提取的 `content_length < 5000` chars 时，应回退尝试更多 CSS 选择器（如 `article`, `main`, `.post-content`, `.entry-content`, `.article-body`, `#content`, `.markdown-body`），确保完整提取。当前脚本仅使用单一主选择器，部分站点（阿里云文档、美团博客、InfoQ）的主内容区域可能被嵌套在多层 `<div>` 容器中，或内容被分割为多个子区域。

### 3. 修复 byteimg CDN 图片下载（case-5）

建议在 SKILL.md 的常见错误部分增加明确规则：byteimg CDN 签名 URL 中的 `~tplv-xxx` 和 `.awebp` 格式图片需要特殊处理——(1) 识别 URL 中 `~tplv` 标记；(2) 解码 `%20` 和 URL-encoded 参数；(3) 识别 `.awebp` 扩展名并加入下载列表；(4) 处理签名过期参数（`x-expires`、`x-signature`）。当前脚本的图片 URL regex 未覆盖 `~` 字符和 `.awebp` 扩展名，导致掘金等 byteimg CDN 站点的图片完全无法下载。

### 4. 修复 WordPress image-table 图片提取（case-7）

建议在 SKILL.md 的常见错误部分增加：WordPress `<table><td><figure><img>` 嵌套结构中的图片需要识别 "image-table" 模式并提取为独立图片引用。AWS 博客等站点将图片包裹在多层 HTML 结构中（`<table>` → `<td>` → `<figure>` → `<img>`），当前脚本仅处理顶层 `<img>` 标签，无法提取嵌套图片。建议在 `extract_images_from_html()` 函数中增加递归查找 `<img>` 的逻辑，或在噪声清理前先提取所有 `<img>` 元素。

### 5. 修复 fill_image_alt_text 正则 bug（已发现并修复）

脚本 `web_to_local_md.py` 第 552 行 `replace_empty_alt()` 函数中 `match.group(2)` 应改为 `match.group(1)`——空图片引用的正则 `r'!\[\]\(([^)]+)\)'` 只有 1 个捕获组，访问 group(2) 会触发 IndexError 导致脚本崩溃。此 bug 在本次评估中已临时修复，建议正式合并到脚本中。

### 6. 改进图片文件名生成策略

建议在 SKILL.md 的步骤 4（Download images）中补充：图片文件名应优先使用人类可读的原始文件名（如从 URL 路径提取 `anthropic-evals-1.png`），而非使用 hash 值（如 `bd42e7b2f3e9bb5218142796d3ede4816588dec0-4584x2580.png`）。参考中 case-1 使用 `anthropic-evals-1.png` 等可读名，而当前输出使用 hash 名，降低了文件可辨识性。

---

*综合评估报告由 evaluate-skill skill 自动生成。核心定位：skill 质量改进的反馈工具，不是绝对质量裁判。*
