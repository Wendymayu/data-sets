# web-to-local-md 综合评估报告（批量模式 — 第二轮）

**评估日期**: 2026-06-22_1600
**Skill 名称**: web-to-local-md
**黄金数据集**: D:\code\opensource\github\data-sets\skills\web-to-local-md\v1
**用例数量**: 7

---

## 总览

| 指标 | 值 | 第一轮对比 |
|------|-----|-----------|
| 测试用例数 | 7 | — |
| 结构通过率 | 91.8% (45/49) | ↑ 87.8% → 91.8% |
| 语义平均分 | 2.54/5 | ↓ 3.29 → 2.54 |
| 综合评分 | 63.1% | ↓ 72.4% → 63.1% |
| 总体评级 | ⭐⭐ | ↓ ⭐⭐⭐ → ⭐⭐ |
| 评估结论 | **需改进** | ↓ 通过 → 需改进 |

**⚠️ 综合评分下降 9.3%，从 ⭐⭐⭐（通过）降为 ⭐⭐（需改进）。原因：本轮发现了第一轮未暴露的 3 个新严重问题。**

---

## 逐用例评分

| 用例 | 结构 | 完整性 | 准确性 | 合规性 | 可用性 | 语义均值 | 回归 | 关键问题 |
|------|------|--------|--------|--------|--------|---------|------|---------|
| case-1 Anthropic | 7/7 ✅ | 5 | 4 | 2 | 4 | 3.75 | ⚠️退化 | 缺发布日期、alt无意义 |
| case-2 阿里云 | 6/7 ⚠️ | 3 | 4 | 2 | 3 | 3.00 | ⚠️退化 | 缺日期、表头错误、内容偏短 |
| case-3 美团 | 7/7 ✅ | 4 | 4 | 2 | 3 | 3.25 | ⚠️退化 | 日期位置错、噪声保留 |
| case-4 InfoQ | 7/7 ✅ | 4 | 4 | 2 | 3 | 3.25 | ⚠️退化 | 推广内容保留、alt无意义 |
| case-5 掘金 | 5/7 ❌ | 1 | 1 | 0 | 1 | 0.75 | ❌严重退化 | **脚本Windows崩溃、0图片下载** |
| case-6 JavaGuide | 7/7 ✅ | 4 | 3 | 3 | 3 | 3.25 | ⚠️退化 | **H1标题UTF-8乱码** |
| case-7 AWS | 6/7 ⚠️ | 2 | 2 | 1 | 2 | 1.75 | ⚠️混合 | **26图片文件下载但markdown零引用** |

---

## 第二轮新发现的严重问题

### 🔴 新问题 1：Strategy A UTF-8 编码损坏（case-6）

case-6 的 H1 标题为乱码 `å¤§æ¨¡åéåºç¡é¢è¯é¢æ»ç»` 而非正确中文 `大模型基础面试题总结`。这是 Strategy A（GitHub 源下载）的编码处理缺陷——GitHub raw `.md` 文件下载后未正确解码 UTF-8。上一轮未发现此问题（可能因首次读取时显示正常，本轮更细致检查时发现）。

**影响**：标题乱码直接影响搜索、阅读体验和 SEO。第一印象极差。

### 🔴 新问题 2：byteimg CDN 文件名导致 Windows 脚本崩溃（case-5）

第一轮中 case-5 的脚本报告 "Downloading 0 images"（跳过了 byteimg 图片）。本轮脚本识别到了 10 张 byteimg 图片并尝试下载，但在保存文件时因文件名包含 `:` 字符（如 `...~tplv-73owjymdk6-jj-mark-v1:0:0:0:0:...`）触发 OSError 崩溃。**Windows 不允许文件名中包含 `:` 字符。**

**影响**：脚本崩溃比跳过图片更严重——用户无法得到任何输出（虽然 index.md 已部分写入，但脚本以 exit code 1 结束）。需要添加 Windows 文件名安全化处理。

### 🔴 新问题 3：图片下载与 markdown 引用脱钩（case-7）

本轮 AWS 博客成功下载了 26 张图片文件（第一轮为 0），这是改进。但 markdown 输出中零个 `![...]()` 图片引用——原图片位置全部用 `| --- |` 空表格占位符替代。26 张图片文件存在于 `images/` 目录但无法在 Typora/VS Code 中看到。

**影响**：图片"下载成功"但"无法看到"，比不下载更令人困惑。用户可能误以为所有图片都成功处理，实际上图片文件和引用完全脱钩。

---

## 逐用例结构断言详情

### case-1（Anthropic 工程博客 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | index.md + 5 images |
| 2 | 文件非空 | ✅ | 42078 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落、表格、代码块 |
| 4 | 无未填充占位符 | ✅ | 无 TODO/TBD/FIXME |
| 5 | 图片引用是本地路径 | ✅ | 5 张图片使用 `images/xxx.png` |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 格式正常 |

通过率: 7/7 (100%)

### case-2（阿里云端到端链路追踪 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | index.md + 4 images |
| 2 | 文件非空 | ✅ | 3971 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 4 张图片使用 `images/p87336x.png` |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ❌ 🟢 | `| --- | --- | --- | --- |` 作为首行，缺少正确表头 |

通过率: 6/7 (85.7%)

### case-3（美团技术团队 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | index.md + 13 images |
| 2 | 文件非空 | ✅ | 8253 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落、表格 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 13 张图片使用 `images/xxx.png` |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 格式正常 |

通过率: 7/7 (100%)

### case-4（InfoQ 阿里云可观测 — Strategy B）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | index.md + 23 images |
| 2 | 文件非空 | ✅ | 10482 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | 23 张图片使用 `images/xxx.png` |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 格式正常 |

通过率: 7/7 (100%)

### case-5（掘金 JetBrains — Strategy B — ❌脚本崩溃）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | index.md 存在（脚本崩溃前写入），但无 images/ 目录 |
| 2 | 文件非空 | ✅ | 7728 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ❌ 🟡 | 全部 10 张图片仍为 byteimg CDN `https://` URL；脚本尝试下载时因文件名含 `:` 在 Windows 上 OSError 崩溃 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ❌ 🟢 | `\*\*text\*\*` 转义粗体；alt 文本含乱码 URL 参数 |

通过率: 5/7 (71.4%)

### case-6（JavaGuide AI 专栏 — Strategy A — ⚠️编码损坏）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | llm-interview-questions.md + 1 image |
| 2 | 文件非空 | ✅ | 5411 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题（**⚠️乱码**）、段落、表格 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅ | `../../images/llm-token-process.png` |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ✅ | 格式正常 |

通过率: 7/7 (100%) — **但 H1 标题内容为 UTF-8 乱码，需在合规性维度扣分**

### case-7（AWS 中国区博客 — Strategy B — ⚠️图片引用脱钩）

| # | 断言 | 结果 | 详情 |
|---|------|------|------|
| 1 | 输出文件存在 | ✅ | index.md + 26 images 文件 |
| 2 | 文件非空 | ✅ | 26325 chars |
| 3 | Markdown 可解析 | ✅ | 含 # 标题、段落 |
| 4 | 无未填充占位符 | ✅ | 无占位符 |
| 5 | 图片引用是本地路径 | ✅* | markdown 中零个 `![...]()` 图片引用；26 张图片文件存在于 images/ 但未被引用 |
| 6 | 占位标记占比 <30% | ✅ | 0% |
| 7 | 无 Markdown 语法损坏 | ❌ 🟢 | 17 处 `| --- |` 无效表格占位符（WordPress image-table 残留） |

通过率: 6/7 (85.7%) — **✅*标注：断言 5 技术通过（无远程 URL），但 26 张图片文件与 markdown 引用完全脱钩，实际不可用**

---

## 逐用例 SKILL.md 合规性评估

### case-1（Anthropic 工程博客）

**完整性 (5/5)**：全文内容完整（42078 chars），涵盖 Introduction → Eval structure → Graders → Agent types → Non-determinism → Roadmap → Conclusion → Appendix 全部板块。5 张图片本地下载。判断依据：index.md 包含所有原文板块和图片。

**准确性 (4/5)**：文本内容事实准确，无编造信息。判断依据：技术术语（pass@k, SWE-bench, 𝜏2-bench 等）与原文一致。扣分：图片 alt 为哈希值（如 `4584x2580`）而非描述性文本（参考中为 `Single-turn vs multi-turn evaluations`）。

**合规性 (2/5)**：违反 2 条 SKILL.md 规则：(1) "Missing publication date" — output 无 `<small style="color:gray">YYYY-MM-DD</small>` 日期标记（参考有 `2026-01-09`）；(2) "Empty image alt text" — `fill_image_alt_text()` 产出哈希值而非有意义描述。判断依据：output line 1-3 无 `<small>` 标签；alt 文本如 `![Bd42e7b2f3e9bb5218142796d3ede4816588dec0 4584x2834]` 不可读。

**可用性 (4/5)**：内容在 Typora 中可正常阅读，图片本地加载。缺少日期和 alt 无意义为小瑕疵，不影响主要内容。

### case-2（阿里云端到端链路追踪）

**完整性 (3/5)**：输出内容仅 3971 chars（参考 7487 chars，约 53%）。主要板块存在但内容偏薄。判断依据：脚本报告 "Strategy B OK: 3971 chars"，明显低于参考内容量。

**准确性 (4/5)**：提取内容事实准确。判断依据：链路追踪、ARMS、OpenTelemetry 内容正确。

**合规性 (2/5)**：违反 2 条规则：(1) 日期缺失；(2) 表格 `| --- | --- | --- | --- |` 作为首行。判断依据：output 无 `<small>` 标签；表格首行为分隔行而非表头行。

**可用性 (3/5)**：内容可阅读但偏短，表格渲染异常。

### case-3（美团技术团队）

**完整性 (4/5)**：核心内容完整，13 张图片下载。但保留噪声行"业务研发平台 2026-05-07"和"算法大模型"。判断依据：output line 5-8 含非正文噪声内容。

**准确性 (4/5)**：核心内容准确。判断依据：AI Coding 管理实践、技术债梳理内容与原文一致。

**合规性 (2/5)**：违反 3 条规则：(1) 日期位置在 H1 上方而非下方（`<small>` 在 line 1，`#` 在 line 3）；(2) alt 文本为哈希值；(3) 噪声内容未清除。判断依据：output line 1 `<small>` 在 line 3 H1 之前；alt 如 `![1c5fff78273feaf4892b46ad3fb757956195300]` 不可读。

**可用性 (3/5)**：可阅读但有噪声干扰和日期位置异常。

### case-4（InfoQ 阿里云可观测）

**完整性 (4/5)**：技术内容完整，23 张图片下载。但尾部保留 AICon 大会推广广告。判断依据：output line 166-170 含推广内容和推广图片。

**准确性 (4/5)**：提取内容准确。判断依据：AIOps、异常检测、PromQL 内容与原文一致。

**合规性 (2/5)**：违反 2 条规则：(1) "Strip noise" — 推广内容未清除；(2) "Empty image alt text" — alt 为哈希值，部分大小写混乱。判断依据：output line 166-170 AICon 推广未移除；alt 如 `![C6ab3...]`、`![Fab...]` 大小写混乱。

**可用性 (3/5)**：可阅读但推广内容影响体验。

### case-5（掘金 JetBrains — ❌ 最严重退化）

**完整性 (1/5)**：文本存在（7728 chars）但 0 张图片下载——脚本在 Windows 因 byteimg 文件名含 `:` 字符 OSError 崩溃。图文重度依赖型文章缺图 = 严重不完整。判断依据：脚本 exit code 1 崩溃，10 张 byteimg 图片未下载。

**准确性 (1/5)**：`\*\*text\*\*` 转义粗体无法正确渲染；所有图片仍指向远程 byteimg 签名 URL（含 `x-expires` 过期参数）。判断依据：output line 53 `\*\*` 格式；图片 URL 含过期时间戳。

**合规性 (0/5)**：几乎违反全部 SKILL.md 规则：无本地图片（违反 Step 4）、alt 文本含乱码 URL 参数（违反 `fill_image_alt_text`）、远程 URL 未替换（违反 Step 5）、噪声未清除（违反 Step 3）、脚本崩溃未 graceful 处理（违反 Implementation "The script handles all steps automatically"）。判断依据：output 所有图片为 CDN URL；脚本崩溃 OSError。

**可用性 (1/5)**：**无法用于离线阅读**——所有图片 URL 为远程链接，离线后全部失效。脚本崩溃也可能导致输出文件不完整。

### case-6（JavaGuide AI 专栏 — ⚠️ UTF-8 编码损坏）

**完整性 (4/5)**：全文内容完整，1 张图片下载，日期存在。判断依据：index.md 包含面试题全文和结构化表格。

**准确性 (3/5)**：H1 标题为 UTF-8 乱码 `å¤§æ¨¡åéåºç¡é¢è¯é¢æ»ç»` 而非正确中文 `大模型基础面试题总结`。这是 Strategy A GitHub 源文件下载的编码处理缺陷。判断依据：output line 1 标题为不可读乱码字符。

**合规性 (3/5)**：大部分规则遵循（日期在 H1 下方 ✅、alt 有意义 ✅、路径正确 ✅）。但 H1 标题编码损坏违反 "extract `<h1>`" 规则——SKILL.md Fix 列说 "Extract `<h1>` or `<title>` before noise stripping; inject as `# title` first line"，标题被提取但编码损坏。判断依据：output line 1 标题乱码。

**可用性 (3/5)**：标题乱码严重影响搜索和第一印象。其余内容可正常阅读。

### case-7（AWS 中国区博客 — ⚠️ 图片引用脱钩）

**完整性 (2/5)**：文本内容完整（26325 chars），26 张图片文件已下载到 images/ 目录。但 **markdown 中零个 `![...]()` 图片引用**——原图片位置全部用 `| --- |` 空表格占位符替代。图片文件与引用完全脱钩。判断依据：Grep 搜索 `![` 在 case-7 output 中找到 0 个匹配；`| --- |` 找到 17 个匹配。

**准确性 (2/5)**：日期位置在 H1 上方（line 1 `<small>` 在 line 3 `#` 之前）；噪声"亚马逊AWS官方博客" header 保留；6 张作者头像作为噪声保留。判断依据：output line 1-3 日期在标题之前；line 1 含 AWS header 噪声。

**合规性 (1/5)**：违反 4 条规则：(1) 图片未在 markdown 中引用（最严重——26 张图片文件存在但 0 个引用）；(2) alt 文本无意义；(3) 噪声未清除（AWS header + 作者头像）；(4) `| --- |` 空表格残留。判断依据：0 个 `![...]` 图片引用；17 处 `| --- |` 占位符；噪声内容保留。

**可用性 (2/5)**：图片文件存在但 markdown 不引用，读者看到 `| --- |` 占位符而非图表。比第一轮 0 图片有改进（文件存在），但引用断裂导致实际不可用。

---

## 回归对比

### case-1（Anthropic）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ⚠️退化 | output 缺 `<small style="color:gray">2026-01-09</small>` 日期 |
| 语义 | ⚠️退化 | alt 为哈希值 vs 参考有意义描述；图片文件名哈希 vs 语义名 |
| 格式 | ⚠️退化 | 代码块缺 `yaml` 语言标注 |

### case-2（阿里云）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ⚠️退化 | 缺日期；内容 3971 chars vs 参考 7487 chars |
| 语义 | ⚠️退化 | 内容量仅参考的 53% |
| 格式 | ⚠️退化 | 表格 `| --- |` 首行问题 |

### case-3（美团）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ⚠️退化 | 日期位置在 H1 上方；保留噪声行 |
| 语义 | —不变 | 核心内容与参考持平 |
| 格式 | ⚠️退化 | 4 张多余噪声图片；日期位置错 |

### case-4（InfoQ）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ⚠️退化 | 缺 alt 有意义描述 |
| 语义 | ⚠️退化 | AICon 推广内容保留（参考已移除） |
| 格式 | —不变 | 格式基本正常 |

### case-5（掘金 — ❌严重退化）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ❌严重退化 | 参考 10 张 .awebp 本地图片 → output 脚本崩溃、0 下载 |
| 语义 | ❌严重退化 | byteimg 签名 URL 含过期时间 → 离线后失效 |
| 格式 | ❌严重退化 | 参考 `**粗体**` → output `\*\*转义\*\*`；参考 `![JetBrains品牌标识]` → output `![乱码URL参数]` |

### case-6（JavaGuide — ⚠️退化）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ⚠️退化 | 参考 `# 大模型基础面试题总结` → output `# å¤§æ¨¡åéåºç¡é¢è¯é¢æ»ç»`（UTF-8 乱码） |
| 语义 | —不变 | 内容完整 |
| 格式 | —不变 | 其他格式正常 |

### case-7（AWS — ⚠️混合：文件改进但引用退化）

| 维度 | 对比 | 详情 |
|------|------|------|
| 结构 | ✅改进 | 图片文件从 0→26 张（WordPress image-table 提取改进） |
| 语义 | ⚠️退化 | markdown 中零个图片引用 vs 参考 17 个；`| --- |` 占位符替代 |
| 格式 | ⚠️退化 | 17 处 `| --- |` 空表格 vs 参考 `![架构图]` |

---

## 共性问题（出现在 ≥3 个用例中）

### 1. 图片 alt 文本无意义（5/7 用例：case-1/2/3/4/7）

`fill_image_alt_text()` 产出哈希派生值（如 `4584x2580`、`P873364`、`1c5fff78273feaf4892b46ad3fb757956195300`）而非人类可读描述。参考中全部有语义 alt（如 `![Single-turn vs multi-turn evaluations]`、`![重构时间线与执行路径]`）。SKILL.md 规定 "derives alt from filename (strip ext, replace -/_ with spaces)"，但对哈希类文件名，strip ext 后仍为不可读字符串。

### 2. 发布日期缺失或位置错误（4/7 用例：case-1/2 缺失，case-3/7 在 H1 上方）

SKILL.md 要求 "Add `<small style="color:gray">YYYY-MM-DD</small>` below the H1 title"，但 case-1/2 完全缺失日期，case-3/7 日期放在 H1 上方而非下方。

### 3. 噪声/推广内容未清除（4/7 用例：case-3/4/5/7）

- case-3：保留 "业务研发平台"、"算法大模型" 噪声行
- case-4：保留 AICon 大会推广广告
- case-5：保留 `[CodeSheep](...)` 作者信息、阅读量
- case-7：保留 "亚马逊AWS官方博客" header、6 张作者头像

SKILL.md 规定 "Strip noise (nav/ads/scripts)"，但未列举具体的噪声文本模式。

### 4. Strategy B 内容提取偏短（3/7 用例：case-2/3/4）

阿里云文档（3971/7487=53%）、美团博客（8253 chars vs 参考 9 张图时的内容）、InfoQ（10482 chars vs 参考 23693 chars）的 Strategy B 提取内容量明显低于参考。

---

## 改进建议

### 1. 增强 alt 文本生成规则（5 用例受影响）

→ SKILL.md **"Common Mistakes" 表格 → "Empty image alt text" 行** 的 Fix 列

当前规则：`fill_image_alt_text()` "derives alt from filename (strip ext, replace -/_ with spaces)"
建议：增加 **fallback 规则**——当文件名派生的 alt 文本为纯数字/哈希（不含 ≥3 个可识别词汇）时，从原始 HTML 的 `<img alt="...">` 属性或相邻 `<figcaption>/<p>` 上下文提取描述性文本作为 alt。在 "Empty image alt text" 行的 Fix 列追加："`fill_image_alt_text()` should fall back to `<img>` tag's `alt` attribute or adjacent `<figcaption>` text when filename-derived alt is unreadable (hash/dimensions-only)."

### 2. 明确日期位置规范（4 用例受影响）

→ SKILL.md **"Common Mistakes" 表格 → "Missing publication date" 行**

当前规则："Add `<small style="color:gray">YYYY-MM-DD</small>` below the H1 title" — "below" 含义模糊
建议：改为 **"Add `<small style="color:gray">YYYY-MM-DD</small>` on the line immediately after the `# title` line, before any other content"**，并明确步骤顺序：(1) extract H1 → first line, (2) date → second line, (3) content follows。确保 `extract_page_metadata()` 在 Strategy B 单页提取路径下也被正确调用。

### 3. 扩展噪声文本模式清单（4 用例受影响）

→ SKILL.md **Quick Reference Step 3 "Strip noise"** + **Implementation 脚本 `NOISE_CLASSES`/`NOISE_TEXT_PATTERNS`**

当前规则："Strip noise (nav/ads/scripts)" — 仅覆盖导航/广告/脚本
建议：增加 **显式噪声文本模式列表**：
- 作者署名块（`[CodeSheep](...)`、"Written by..."、"作者：..."）
- 阅读量/点赞数（`19,835`、`阅读6分钟`、`次浏览`）
- 网站频道 header（"亚马逊AWS官方博客"、"业务研发平台"、"算法大模型"）
- 推广内容块（会议广告 "AICon|QCon|ArchSummit"、课程推荐）
- 作者头像图片（小尺寸 .jpg 含人名关键词）

### 4. 添加 Windows 文件名安全规则（case-5 脚本崩溃）🔴

→ SKILL.md **"Common Mistakes" 表格 → 新增行**

| Mistake | What happens | Fix |
|---------|-------------|------|
| Windows-invalid characters in filenames (`:`, `?`, `*`, `<`, `>`, `|`) | Script crashes with OSError on Windows; images cannot be saved | Sanitize filenames by replacing Windows-invalid characters with `_` before saving. Add graceful fallback: if image download fails, log error and continue (don't crash entire script) |

### 5. 确保图片引用与文件同步（case-7 关键问题）🔴

→ SKILL.md **Quick Reference Step 5 "Fix paths"** + **Implementation 脚本路径替换逻辑**

问题：26 张图片文件已下载但 markdown 中零个图片引用——WordPress `<table><td><figure><img>` 嵌套结构的 `<img>` 标签未被正确转换为 Markdown `![alt](path)` 语法，而是变成了 `| --- |` 空表格占位符。
建议：在 Step 5 "Fix paths" 中增加 **验证步骤**——"After path replacement, verify that every file in `images/` directory is referenced at least once in the output markdown. If any image file has zero references, log a warning and attempt to re-inject the image reference at the correct position using the original HTML `<img>` tag mapping." 同时在脚本中增加 WordPress image-table 检测逻辑：当 `<table>` 仅含 `<img>` 元素（无实际表格数据）时，应将 `<table>` → `<figure>` → `<img>` 转换为独立 `![alt](path)` 图片引用而非 `| --- |` 占位符。

### 6. Strategy A UTF-8 编码检测（case-6 标题乱码）🔴

→ SKILL.md **Quick Reference Step 2 "Get source files → GitHub raw URLs"**

问题：case-6 H1 标题为 UTF-8 乱码（`å¤§æ¨¡åéåºç¡é¢è¯é¢æ»ç»` 而非 `大模型基础面试题总结`）——GitHub 源 `.md` 文件下载后未正确处理编码。
建议：在 Step 2 增加说明："When downloading `.md` files from GitHub for Strategy A, enforce UTF-8 encoding using `content.decode('utf-8')`. If the first line contains mojibake (non-readable characters), attempt re-download with explicit encoding conversion or detect encoding via `chardet`. Verify that the H1 title line is readable before proceeding."

### 7. 修复 fill_image_alt_text 正则 bug（第一轮已发现）

脚本第 552 行 `replace_empty_alt()` 中 `match.group(2)` 应改为 `match.group(1)`——正则 `r'!\[\]\(([^)]+)\)'` 只有 1 个捕获组。此 bug 已临时修复，需正式合并。

---

## 第一轮 vs 第二轮对比

| 指标 | 第一轮 | 第二轮 | 变化 |
|------|--------|--------|------|
| 结构通过率 | 87.8% | 91.8% | ↑4% |
| 语义平均分 | 3.29 | 2.54 | ↓0.75 |
| 综合评分 | 72.4% | 63.1% | ↓9.3% |
| 总体评级 | ⭐⭐⭐ | ⭐⭐ | ↓1级 |
| 评估结论 | 通过 | 需改进 | ↓ |

**第二轮评分更严格且发现了新严重问题**：
1. Strategy A UTF-8 编码损坏（case-6 H1 乱码）——第一轮未发现
2. Windows byteimg 文件名崩溃（case-5 OSError）——第一轮为跳过图片，本轮为脚本崩溃
3. 图片引用脱钩（case-7 26张文件下载但0引用）——第一轮为0下载，本轮改进为26下载但引用断裂

---

*综合评估报告由 evaluate-skill skill 自动生成（第二轮）。核心定位：skill 质量改进的反馈工具，不是绝对质量裁判。*
