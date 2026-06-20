# web-to-local-md Golden Test Data v1

Strategy B (HTML→MD) 和 Strategy A (GitHub 源文件) 的黄金测试数据集，用于验证 `web-to-local-md` 技能的转换质量。

## 目录结构

```
case-{N}/
  input.yaml          # 测试输入（URL、策略、难度等）
  reference/
    index.md           # 黄金输出 markdown
    images/            # 本地化图片
```

特殊：case-6 有嵌套子目录 `reference/ai/interview-questions/`，子页面的图片引用使用 `../../images/` 相对路径。

## 用例一览

| Case | 来源网站 | 数据 URL | 策略 | 语言 | 难度 | 图片数 | 说明 |
|------|---------|----------|------|------|------|--------|------|
| 1 | Anthropic Engineering Blog | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | B | en | medium | 5 | 英文工程博客，标准 HTML 结构，图片居中 |
| 2 | 阿里云文档 | https://www.alibabacloud.com/help/zh/opentelemetry/use-cases/alibaba-cloud-end-to-end-link-tracing-best-practices | B | zh | easy | 4 | 中文云文档，图片 URL 含哈希 ID |
| 3 | 美团技术团队 | https://tech.meituan.com/2026/05/07/Agent-AI-Coding.html | B | zh | medium | 9 | 中文技术博客，含 .jpg 和 .png 混合图片 |
| 4 | InfoQ 中文 | https://www.infoq.cn/article/C9L0B5pMbKLOTiiUeYk7 | B | zh | hard | 23 | InfoQ 部分页面有 SSR HTML，图片多、含 .jpeg |
| 5 | 掘金 | https://juejin.cn/post/7622177349912952878 | B | zh | hard | 10 | ByteDance CDN 使用 .awebp 格式（WebP 变体） |
| 6 | JavaGuide (VuePress) | https://javaguide.cn/ai/interview-questions/llm-interview-questions.html | A | zh | easy | 1 | Strategy A：GitHub 源文件，嵌套子目录结构 |
| 7 | AWS 中国博客 | https://aws.amazon.com/cn/blogs/china/practical-guide-to-building-agentic-ai-applications-for-aws-china-region/ | B | zh | hard | 17 | WordPress 图片嵌套在 `<table><td><figure><img>` 中，25 个代码块 |

## 策略说明

- **Strategy A**：从 GitHub 仓库直接下载源 `.md` 文件（质量最佳）
- **Strategy B**：从网页 HTML 提取转换（需处理 SPA、CDN 签名、图片嵌套等）

## 图片路径规则

- 根目录级别的 `.md` 文件：使用 `images/xxx.png`
- 子目录级别的 `.md` 文件（如 `ai/interview-questions/`）：使用 `../../images/xxx.png`
- 图注使用 `<center>` 标签居中
