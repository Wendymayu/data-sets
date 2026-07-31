#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_hf_dataset.py — 从 HuggingFace 下载 dataset / model 仓库的全部文件。

绕开两个会让人卡很久的坑：
  1) Windows + 国内镜像(hf-mirror.com) 下，gated 的 LFS 文件 etag 会被掩码成
     "****"，huggingface_hub 拿它拼 .incomplete 临时文件名 -> [WinError 123]
     (Windows 文件名不允许 '*')，下载还没开始就崩。
  2) 带 token 的 requests/urllib GET，在 resolve -> 签名 CDN 的跨域 302 跳转里
     会被剥掉 Authorization，落回 huggingface.co 触发 401。

本脚本：用 /api/.../tree?recursive=1 列文件(JSON)，再对每个文件
`curl -sL --fail -H "Authorization: Bearer <token>"` 下载 —— curl -L 会跟 302 到
签名 CDN，并正确地不给 CDN 发 auth(CDN 用签名 URL，不需要)。

依赖：Python 3 标准库 + 系统 curl(Windows 10+ 自带 curl.exe；Git Bash/macOS/Linux 都有)。

用法见同目录 README.md。
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_MIRROR = "https://hf-mirror.com"
OFFICIAL = "https://huggingface.co"


def read_token(arg_token):
    """token 优先级: 命令行 > $HF_TOKEN > ./.hf_token > ~/.cache/huggingface/token"""
    if arg_token:
        return arg_token.strip()
    env = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if env:
        return env.strip()
    local = pathlib.Path(".hf_token")
    if local.exists():
        return local.read_text(encoding="utf-8").strip()
    cached = pathlib.Path.home() / ".cache" / "huggingface" / "token"
    if cached.exists():
        return cached.read_text(encoding="utf-8").strip()
    return ""


def list_files(base, repo_type, repo, token):
    """调用 /api/{repo_type}s/{repo}/tree/main?recursive=1 列出所有文件，自动翻页。"""
    url = f"{base}/api/{repo_type}s/{repo}/tree/main?recursive=1"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    paths = []
    while url:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                link = resp.headers.get("Link", "")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            sys.exit(f"列文件失败: HTTP {exc.code}\n{body}\n"
                     f"(gated 仓库? 用 --token 或设 $HF_TOKEN，并先在网页上 Request access)")
        for item in data:
            if item.get("type") == "file":
                paths.append(item["path"])
        # 翻页: Link 头里的 rel="next"
        url = ""
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1:part.find(">")]
                if url and not url.startswith("http"):
                    url = base + url
                break
    return paths


def download_file(base, repo_type, repo, path, token, dest):
    """用 curl -sL --fail 下单个文件到 dest.part，成功后原子改名。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    if part.exists():
        part.unlink()                      # 不做单文件断点续传；重跑整文件(正确性优先)
    url = f"{base}/{repo_type}s/{repo}/resolve/main/{path}"
    cmd = ["curl", "-sL", "--fail", "--retry", "3", "--retry-delay", "2"]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += ["-o", str(part), url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and part.exists() and part.stat().st_size > 0:
        part.replace(dest)
        return True, dest.stat().st_size
    return False, res.stderr.strip()[:160]


def main():
    ap = argparse.ArgumentParser(
        description="下载 HuggingFace dataset/model 仓库(绕开 Windows+镜像的 etag/auth 坑)")
    ap.add_argument("repo", help="仓库 ID, 如 gaia-benchmark/GAIA")
    ap.add_argument("--repo-type", default="dataset", choices=["dataset", "model"],
                    help="dataset 或 model, 默认 dataset")
    ap.add_argument("--token", help="HF token; 省略则读 $HF_TOKEN/.hf_token/huggingface-cli 缓存")
    ap.add_argument("--out", help="输出目录, 默认 ./<仓库名>")
    ap.add_argument("--mirror", default=DEFAULT_MIRROR,
                    help=f"端点, 默认国内镜像 {DEFAULT_MIRROR}; 官方用 {OFFICIAL}")
    ap.add_argument("--subset", help="只下某路径前缀, 如 2023/validation")
    args = ap.parse_args()

    token = read_token(args.token)
    repo = args.repo.strip("/")
    out_dir = pathlib.Path(args.out) if args.out else pathlib.Path(repo.split("/")[-1])
    base = args.mirror.rstrip("/")

    files = list_files(base, args.repo_type, repo, token)
    if args.subset:
        files = [f for f in files if f.startswith(args.subset)]
    print(f"{len(files)} 个文件待下载 -> {out_dir}  (端点: {base}, repo: {repo})")

    ok = failed = skipped = 0
    for i, path in enumerate(files, 1):
        dest = out_dir / path
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            continue
        good, info = download_file(base, args.repo_type, repo, path, token, dest)
        if good:
            ok += 1
            print(f"[{i}/{len(files)}] ok   {path}  ({info} bytes)")
        else:
            failed += 1
            print(f"[{i}/{len(files)}] ERR  {path}  -> {info}")
    print(f"\nsummary: ok={ok} skipped={skipped} failed={failed} total={len(files)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
