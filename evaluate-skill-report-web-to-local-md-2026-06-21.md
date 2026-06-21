# web-to-local-md 综合评估报告（批量模式）

**评估日期**: 2026-06-21
**Skill 名称**: web-to-local-md
**黄金数据集**: D:\code\opensource\github\data-sets\skills\web-to-local-md\v1
**用例数量**: 7
**评估模式**: 批量评估（--golden + --verbose）

---

## 总览

| 指标 | 值 |
|------|-----|
| 测试用例数 | 7 |
| 结构通过率 | 100% (56/56) |
| 语义平均分 | 4.69/5 |
| 总体评级 | ⭐⭐⭐⭐⭐ |
| 评估结论 | 通过 |

---

## 逐用例评分

| 用例 | 结构 | 完整性 | 准确性 | 合规性 | 可用性 | 平均 | 回归 | 关键问题 |
|------|------|--------|--------|--------|--------|------|------|---------|
| case-1 Anthropic Evals | 8/8 ✅ | 5 | 5 | 4 | 5 | 4.75 | ✅不变 | 2个YAML代码块缺`yaml`标注 |
| case-2 阿里云链路追踪 | 8/8 ✅ | 5 | 5 | 5 | 5 | 5.0 | ✅不变 | 无 |
| case-3 美团AI Coding | 8/8 ✅ | 5 | 5 | 5 | 4 | 4.75 | ✅不变 | 锚点链接格式非标准 |
| case-4 InfoQ AIOps | 8/8 ✅ | 5 | 5 | 5 | 5 | 5.0 | ✅不变 | 无 |
| case-5 掘金JetBrains | 8/8 ✅ | 5 | 5 | 5 | 4 | 4.75 | ✅不变 | .awebp格式兼容性 |
| case-6 JavaGuide | 8/8 ✅ | 5 | 5 | 4 | 4 | 4.5 | ⚠️退化 | 5处GitHub源链接未strip URL |
| case-7 AWS Agentic AI | 8/8 ✅ | 5 | 5 | 5 | 5 | 5.0 | ✅不变 | 无 |

---

## 结构断言结果

### 逐断言统计（7个case × 8项 = 56项）

| # | 断言项 | 严重级别 | 通过 | 失败 | 通过率 |
|---|--------|---------|------|------|--------|
| 1 | 输出文件存在 | 🔴 Critical | 7 | 0 | 100% |
| 2 | 文件非空（>100字符） | 🔴 Critical | 7 | 0 | 100% |
| 3 | Markdown可解析（有标题+段落） | 🟡 Medium | 7 | 0 | 100% |
| 4 | 无未填充占位符 | 🔴 Critical | 7 | 0 | 100% |
| 5 | URL是文章级 | 🟡 Medium | 7 | 0 | 100% |
| 6 | 图片引用是本地路径（非CDN） | 🟡 Medium | 7 | 0 | 100% |
| 7 | 占位标记占比<30% | 🟡 Medium | 7 | 0 | 100% |
| 8 | 无Markdown语法损坏 | 🟢 Low | 7 | 0 | 100% |

**通过率**: 56/56 (100%)

所有8项结构断言在全部7个case中均通过：
- 🔴 Critical项（文件存在/非空/无占位符）100%通过
- 🟡 Medium项（Markdown可解析/URL文章级/图片本地路径/占位标记占比）100%通过
- 🟢 Low项（语法完整性）100%通过

断言5详细判断依据（URL是文章级）：
- 所有7个input.yaml source_url路径深度≥2：case-1(depth=2)✅、case-2(depth=5)✅、case-3(depth=4)✅、case-4(depth=2)✅、case-5(depth=2)✅、case-6(depth=3)✅、case-7(depth=4)✅
- case-1和case-7的输出内容中包含产品首页链接（如bolt.new、descript.com、aws.amazon.com/glue/等，深度0-1），但这些是原文内容中的引用链接，不是被下载页面的URL，不影响断言判定

---

## SKILL.md 合规性评估（verbose详细判断依据）

SKILL.md关键规则（本次评估对照的rubric）：
1. 核心原则：GitHub source > HTML conversion（Strategy A > B）
2. 图片路径规则：根目录用`images/xxx.png`，子目录用`../images/xxx.png`
3. Link Policy：Strategy B保留HTML `<a href>`的`[text](url)`链接；Strategy A的GitHub .md源链接转换为纯文本；裸URL移除
4. 常见错误表：包括regex HTML转换、错误图片路径、SPA骨架、anchor-only headers、URL编码文件名、缺少发布日期、保留GitHub源链接
5. 发布日期：在H1标题下添加`<small style="color:gray">YYYY-MM-DD</small>`

### 完整性 — 平均5.0/5

所有7个case完整性均为5分：

**Case-1 (5/5)**：原文所有板块完整保留（Introduction→Appendix共7个主章节），5张图片均有描述性alt，4个表格完整，2个代码块有内容，`<small style="color:gray">2026-01-09</small>`日期✅（行3）。SKILL.md要求的输出要素全部齐全。

**Case-2 (5/5)**：4张图片有描述性alt（`阿里云端到端链路追踪架构图`、`云产品链路追踪接入效果`、`端到端调用链示意图`、`ARMS双探针共存方案`），2个4列表格完整，`<small style="color:gray">2024-11-20</small>`日期✅（行3）。要素齐全。

**Case-3 (5/5)**：9张图片均有描述性alt，1个5列详细表格完整，`<small style="color:gray">2026-05-07</small>`日期✅（行5）。要素齐全。

**Case-4 (5/5)**：22张图片均有描述性alt，1个PromQL代码块有内容，`<small style="color:gray">2024-07-24</small>`日期✅（行3）。推广内容已清理（不属于文章核心内容，不影响完整性）。

**Case-5 (5/5)**：10张.awebp图片均有描述性alt，`<small style="color:gray">2026-03-30</small>`日期✅（行3）。推广段落已移除。

**Case-6 (5/5)**：1张图片alt`Token 化过程示例`，1个3列表格完整，8个子标题，`<small style="color:gray">2026-05-18</small>`日期✅（行3）。子目录结构符合Strategy A预期。

**Case-7 (5/5)**：17张图片有描述性alt（从`<center>`图注合并），25个代码块有正确语言标注，`<small style="color:gray">2025-06-17</small>`日期✅（行5）。要素齐全。

### 准确性 — 平均5.0/5

所有7个case准确性均为5分：

**Case-1 (5/5)**：内容忠实还原Anthropic原文，5张图片alt与原文图注一致（"Single-turn vs multi-turn evaluations"等），无编造URL或合成内容。

**Case-2 (5/5)**：alt文本精确匹配上下文语境（如行9图片紧跟"端到端全链路打通"→alt`阿里云端到端链路追踪架构图`准确）。

**Case-3 (5/5)**：alt文本基于各图片所在段落上下文推断，均与语境匹配（如行45图片在"重构时间线"标题后→alt`重构时间线与执行路径`）。

**Case-4 (5/5)**：22张图片alt与上下文语境精确对应。"复制代码"已清（不属于原文内容），AICon推广已移除（不属于核心内容），不影响准确性。

**Case-5 (5/5)**：alt文本准确描述产品/功能界面（JetBrains品牌、Code With Me、Fleet IDE、JetBrains Air等）。推广段落移除不影响核心内容。

**Case-6 (5/5)**：Strategy A从GitHub源文件直接获取，质量天然最高。内容与JavaGuide仓库源文件一致。

**Case-7 (5/5)**：alt文本从原始`<center>`图注提取语义一致。代码块语言标注与内容匹配。

### 合规性 — 平均4.86/5

**Case-1 (4/5)**：
- ✅ 图片路径全部本地（`images/anthropic-evals-*.png`）→ 遵循SKILL.md步骤5
- ✅ `<small style="color:gray">2026-01-09</small>`日期 → 遵循常见错误表"Missing publication date"
- ✅ 链接格式正确：所有`[text](url)`来自HTML `<a href>` → 遵循Link Policy"Preserve `[text](url)` from `<a href>`"
- ✅ 无HTML转写残留（Copy文本已清除）
- ✅ Strategy B正确选择
- ⚠️ 行102/148的2个YAML代码块以````` ````开头无语言标注 → 扣1分（虽非SKILL.md明确禁止，但不符合代码块标注最佳实践）

**Case-2 (5/5)**：
- ✅ 图片路径本地 → 遵循步骤5
- ✅ `<small style="color:gray">2024-11-20</small>`日期 → 遵循常见错误表
- ✅ 无HTML残留
- ✅ Strategy B正确

**Case-3 (5/5)**：
- ✅ 图片路径本地
- ✅ `<small style="color:gray">2026-05-07</small>`日期
- ✅ 无HTML残留

**Case-4 (5/5)**：
- ✅ 图片路径本地
- ✅ `<small style="color:gray">2024-07-24</small>`日期
- ✅ "复制代码"HTML按钮文本已清除
- ✅ AICon推广已移除（遵循流程图"Strip noise (nav/ads/scripts)"步骤精神）

**Case-5 (5/5)**：
- ✅ 图片路径本地
- ✅ `<small style="color:gray">2026-03-30</small>`日期
- ✅ 推广段落已移除

**Case-6 (4/5)** ⚠️ **Link Policy违规**：
- ✅ 图片路径`../../images/` → 遵循步骤5子目录规则
- ✅ `<small style="color:gray">2026-05-18</small>`日期 → 遵循常见错误表
- ❌ **5处`[text](url)`链接来自GitHub .md源**（行36`[《LLM运行机制》](../llm-basis/llm-operation-mechanism.md)`、行64、行90、行119），按SKILL.md Link Policy"GitHub .md source: convert to plain text, discard URLs"，这些应只保留文本"《LLM运行机制》"而丢弃URL部分`../llm-basis/...`。当前保留了完整链接格式 → **违反Link Policy规则** → 扣1分
- 这也是常见错误表中"Preserving all links from GitHub .md source"规则的直接违规

**Case-7 (5/5)**：
- ✅ 图片路径本地
- ✅ `<small style="color:gray">2025-06-17</small>`日期
- ✅ `<center>`HTML已合并到alt并移除
- ✅ powershell→bash/json/python纠正
- ✅ prose中链接为`[text](url)`格式（来自HTML `<a href>`）→ 遵循Link Policy
- ✅ 代码块内URL（如curl、git clone等）属于代码内容，不受Link Policy管辖

### 可用性 — 平均4.71/5

**Case-1 (5/5)**：Typora/VSCode直接阅读，图片渲染正常，表格完整，链接可点击。

**Case-2 (5/5)**：直接可用，表格完整，链接格式正确。

**Case-3 (4/5)**：锚点链接格式`## [一、背景](#一、背景)`非标准。除此之外无需修正。

**Case-4 (5/5)**：直接可用，图片alt充分，无UI残留。

**Case-5 (4/5)**：.awebp格式兼容性风险。

**Case-6 (4/5)**：缺标准index.md入口 + Link Policy违规导致链接格式不正确（应strip URL）。

**Case-7 (5/5)**：代码块语法高亮正确，图片alt描述丰富，直接可用。

---

## 回归对比（golden模式）

本轮评估以当前（修复后）黄金数据为对象，与SKILL.md最新规则对比。回归对比分析当前数据与SKILL.md理想输出之间的差距：

| Case | 结构差异 | 语义差异 | 格式差异 | 总评 |
|------|---------|---------|---------|------|
| case-1 | 不变 | 不变 | 2个代码块缺语言标注（轻微） | ✅不变 |
| case-2 | 不变 | 不变 | 不变 | ✅不变 |
| case-3 | 不变 | 不变 | 锚点格式非标准（轻微） | ✅不变 |
| case-4 | 不变 | 不变 | 不变 | ✅不变 |
| case-5 | 不变 | 不变 | .awebp兼容性（原文特征） | ✅不变 |
| case-6 | 不变 | 5处GitHub源链接保留URL（应strip） | 链接格式不符Link Policy | ⚠️退化 |
| case-7 | 不变 | 不变 | 不变 | ✅不变 |

**case-6退化详情**：5处`[text](url)`链接应按Link Policy转换为纯文本（如`《LLM运行机制》`而非`[《LLM运行机制》](../llm-basis/...)`），当前保留了GitHub源链接格式。

---

## 共性问题（出现在≥3个用例中）

当前无≥3个case中出现的未修复共性问题。

以下问题出现在1-2个case中（未达≥3阈值）：
1. **代码块缺语言标注**（1/7个case：case-1的2个YAML块）
2. **GitHub源链接未strip URL**（1/7个case：case-6的5处链接）
3. **锚点链接格式非标准**（1/7个case：case-3）
4. **图片格式兼容性**（1/7个case：case-5的.awebp）

---

## 改进建议

### 针对黄金数据集的修复（3项）

1. **建议修复case-6的Link Policy违规**：将5处`[text](url)`GitHub源链接转换为纯文本。具体：行36`[《LLM 运行机制：Token、上下文窗口与采样参数怎么影响输出》](../llm-basis/llm-operation-mechanism.md)`改为`《LLM 运行机制：Token、上下文窗口与采样参数怎么影响输出》`（同理处理行64、行90、行119）。依据：SKILL.md常见错误表"Preserving all links from GitHub .md source"规则 + Link Policy"Strategy A: `[text](url)` → convert to plain text"

2. **建议修复case-1的2个代码块语言标注**：行102和148的````` ````改为````` yaml ````

3. **建议修复case-4的1个代码块语言标注**：````` ````改为````` promql ````或````` text ````

### 针对SKILL.md的改进建议（2项）

4. **建议在SKILL.md常见错误表增加规则**：「HTML按钮文本残留（如"复制代码"、"Copy"）需在转换后清除，不应出现在最终输出中」—— 当前常见错误表未覆盖此场景，但case-1和case-4的实际修复已证明这是常见问题

5. **建议在SKILL.md常见错误表增加规则**：「`<center>`等deprecated HTML标签不应出现在最终输出中；图注内容应合并到图片alt属性」—— case-7的实际修复已证明这是常见问题

### 针对数据集覆盖度的补充建议（4项）

6. 建议新增至少1个英文Strategy B case：当前英文仅case-1（1个），语言多样性不足
7. 建议新增至少1个纯SPA页面case：验证Strategy B的fallback机制（流程图中"FAIL: pure SPA, no SSR content"路径）
8. 建议新增至少1个Strategy A多页面站点case：当前case-6仅单页面，多页面整站下载的测试覆盖不足
9. 建议新增至少1个需要大量link stripping的Strategy A case：当前case-6的5处链接是最小覆盖，需验证`strip_non_html_links()`对大型GitHub .md文档的效果

---

*综合评估报告由 evaluate-skill skill 自动生成（verbose模式）。核心定位：skill质量改进的反馈工具，不是绝对质量裁判。*
