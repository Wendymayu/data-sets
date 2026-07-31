# HuggingFace 数据集 / 模型 下载指南

`download_hf_dataset.py` —— 一个**不依赖 `huggingface_hub`**、能在 Windows + 国内镜像下稳定下载 gated/公开仓库的脚本。

## 为什么不用 `huggingface_hub.snapshot_download`

它在这套环境下有两个坑（亲历，GAIA 数据集）：

1. **Windows + 镜像 + gated LFS 的星号 etag**：镜像对 gated LFS 文件返回的 etag 被掩码成 `****`，`huggingface_hub` 拿它拼 `.incomplete` 临时文件名，而 Windows 文件名不允许 `*` → `[WinError 123]`，下载还没开始就崩。
2. **`requests` GET 的 401**：带 token 的 `requests` 直接 GET `resolve`，在 `resolve → 签名 CDN` 的跨域 302 跳转里会被剥掉 `Authorization`，落回 huggingface.co 触发 `401`。

本脚本绕开两者：用 `/api/.../tree?recursive=1` 列文件，再逐个 `curl -sL --fail -H "Authorization: Bearer <token>"` 下载——`curl -L` 会跟 302 到签名 CDN，并正确地不给 CDN 发 auth（CDN 用签名 URL，不需要）。

## 前置

- Python 3.8+（仅用标准库，无需 `pip install` 任何包）
- `curl`（Windows 10+ 自带 `curl.exe`；Git Bash / macOS / Linux 都有）
- gated 数据集需要 HF token

## 获取 token 和 gated 访问权

1. 注册并登录 https://huggingface.co
2. 建 token：https://huggingface.co/settings/tokens → New token → 类型 **Read**
3. gated 数据集（如 GAIA）：打开其页面 → 点 **Request access**（`gated: auto` 的会秒批）

## 用法

切到想放数据的目录，运行：

```bash
# 公开数据集（无需 token）
python download_hf_dataset.py <用户>/<仓库>

# gated 数据集（带 token）
python download_hf_dataset.py gaia-benchmark/GAIA --token hf_xxxxxxxx

# 模型仓库
python download_hf_dataset.py <用户>/<模型> --repo-type model --token hf_xxx

# 只下某子目录（如 GAIA 的 validation）
python download_hf_dataset.py gaia-benchmark/GAIA --token hf_xxx --subset 2023/validation

# 不走镜像，用官方端点（网络能直连 HF 时）
python download_hf_dataset.py <repo> --mirror https://huggingface.co --token hf_xxx
```

文件落在 `./<仓库名>/` 下，保持仓库原目录结构。**重跑会跳过已下完的文件**（按存在且非空判断）。

## 三种提供 token 的方式（任选其一）

- 命令行 `--token hf_xxx`
- 环境变量 `HF_TOKEN=hf_xxx`（或写进 shell profile）
- 当前目录放 `.hf_token` 文件（内容就是 token）——**如果在 git 仓库里，务必把 `.hf_token` 加进 `.gitignore`**
- 跑过 `huggingface-cli login` 也行，脚本会自动读 `~/.cache/huggingface/token`

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| `403 GatedRepo` / 列文件失败 401 | 没带 token，或没在网页上 Request access。先 request access，再 `--token`。 |
| `[WinError 123]` 星号文件名 | 你在用 `huggingface_hub`。换本脚本。 |
| 官方端点连不上 / 超时 | 用默认镜像 `--mirror https://hf-mirror.com`（已是默认）。 |
| 镜像也慢 / 断 | 加 `--mirror https://huggingface.co` 对比；或重跑（跳过已完成）。 |
| 某个超大单文件想断点续传 | 脚本默认不做单文件 resume；可在 `download_file` 的 curl 命令加 `-C -`。 |

## 小贴士

- gated 数据集（如 GAIA）的 **test** split 的 `metadata.parquet` 里 `answer` 字段可能为空/隐藏——这是榜单设计，不是下载问题。
- 想验证完整性：下完后再跑一次脚本，应得到 `ok=0 skipped=N failed=0`。
- token 别外泄；用完或曾明文贴出过就去 settings/tokens 轮换。
