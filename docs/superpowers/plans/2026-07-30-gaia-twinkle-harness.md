# GAIA → Twinkle 评测 Harness 实现计划（基础版）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用本地 mini 样本驱动 twinkle 答题，归一化精确匹配打分，产出准确率报告。

**Architecture:** 独立 WS 客户端（仅依赖 `websockets`，不 import twinkle），手搓 E2A 信封直连 AgentServer :18000；顺序跑样本，逐题打分，写报告。

**Tech Stack:** Python 3.11+ / `websockets` / stdlib / pytest。

---

## 约定（所有任务通用）

- **Python 解释器**：用 twinkle 的 venv，它已含 `websockets` + `pytest`，**无需安装任何依赖**。
  每次开终端先激活：
  ```bash
  . D:/code/opensource/github/twinkle/.venv/Scripts/activate   # Git Bash
  ```
  之后 `python` 即该 venv 解释器。
- **工作目录**：所有命令在 `D:/code/opensource/github/data-sets` 根目录执行。
- **跑测试**：`python -m pytest gaia_twinkle/tests/<file> -v`（`-m` 会把 cwd 放上 sys.path，使 `gaia_twinkle` 包可导入）。
- **commit 只 add 本任务相关文件**，不碰工作区里未跟踪的 `jiuwenclaw/`、`output/`。

## 文件结构

```
data-sets/
  conftest.py                        # 空：标记 data-sets 为 pytest rootdir
  gaia_twinkle/
    __init__.py
    scorer.py                        # normalize() + score()（纯函数）
    twinkle_client.py                # TwinkleClient.ask()（WS → AgentServer）
    runner.py                        # Sample / TaskResult / load_samples / extract_answer / run_task / run_all
    reporter.py                      # write_report()
    run_gaia.py                      # CLI：build_parser / parse_args / main
    samples/
      mini_gaia.jsonl                # 6 条样本
      attachments/
        capitals.csv
        sales.csv
    tests/
      conftest.py                    # sys.path 注入 + 假 AgentServer fixture
      test_scorer.py
      test_twinkle_client.py
      test_runner.py
      test_reporter.py
    .gitignore                       # 忽略 output/
    README.md
```

---

## Task 1: Scorer 模块（归一化 + 匹配）

**Files:**
- Create: `gaia_twinkle/__init__.py`
- Create: `gaia_twinkle/scorer.py`
- Create: `data-sets/conftest.py`
- Test: `gaia_twinkle/tests/test_scorer.py`

- [ ] **Step 1: 建包骨架 + 空 conftest**

`gaia_twinkle/__init__.py`：
```python
"""GAIA → Twinkle 评测 harness（基础版）。"""
```

`data-sets/conftest.py`：
```python
# 标记 data-sets 为 pytest rootdir。空文件即可。
```

- [ ] **Step 2: 写失败测试**

`gaia_twinkle/tests/test_scorer.py`：
```python
from gaia_twinkle.scorer import normalize, score


def test_normalize_lowercases():
    assert normalize("Paris") == "paris"


def test_normalize_strips_punctuation_and_articles():
    assert normalize("The Eiffel Tower!") == "eiffel tower"
    assert normalize("a cat") == "cat"


def test_normalize_thousands_and_decimal():
    assert normalize("1,000") == "1000"
    assert normalize("1.0") == "1"
    assert normalize("3.14") == "3.14"  # decimal preserved


def test_normalize_unicode_nfkc():
    assert normalize("Gabriel García Márquez") == "gabriel garcia marquez"


def test_score_exact_and_substring():
    assert score("Paris", "Paris") is True
    assert score("Paris, France", "Paris") is True  # substring
    assert score("London", "Paris") is False


def test_score_number_normalization():
    assert score("1,000", "1000") is True
    assert score("1.0", "1") is True


def test_score_empty_gold_only_matches_empty():
    assert score("", "") is True
    assert score("anything", "") is False
```

- [ ] **Step 3: 跑测试，确认 FAIL（模块不存在）**

Run: `python -m pytest gaia_twinkle/tests/test_scorer.py -v`
Expected: `ModuleNotFoundError: No module named 'gaia_twinkle.scorer'`

- [ ] **Step 4: 实现 scorer**

`gaia_twinkle/scorer.py`：
```python
"""GAIA 风格答案打分：归一化 + 精确/子串匹配。

NOTE: 官方 GAIA scorer 未拉到（HF gated + 本机网络封），本版为合理近似；
接真数据时按官方脚本对齐（spec §10）。
"""
from __future__ import annotations

import re
import unicodedata

_ARTICLES = {"a", "an", "the"}


def normalize(answer: str) -> str:
    """归一化：NFKC、小写、去千分位逗号、去整数值的 .0、去标点、去前导冠词、压空白。"""
    if not answer:
        return ""
    s = unicodedata.normalize("NFKC", str(answer)).lower().strip()
    # 千分位：1,000 -> 1000（逗号夹在数字间、后跟 3 位 + 非数字/结尾）
    s = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", s)
    # 整数值小数：1.0 -> 1（.0+ 后接非数字或结尾）
    s = re.sub(r"(\d)\.0+(?=\D|$)", r"\1", s)
    # 去标点：保留 \w 与 "."（小数点），其余转空格
    s = re.sub(r"[^\w.]+", " ", s, flags=re.UNICODE)
    tokens = [t.strip(".") for t in s.split() if t.strip(".")]
    while tokens and tokens[0] in _ARTICLES:
        tokens = tokens[1:]
    return " ".join(tokens)


def score(prediction: str, gold: str) -> bool:
    """归一后预测 == 金标，或金标为预测子串即判对。

    已知瑕疵：短金标（如 "1"）会子串误匹配无关预测（如 "100"）。首版接受，
    接真数据时对齐官方 scorer。
    """
    np = normalize(prediction)
    ng = normalize(gold)
    if not ng:
        return not np
    return np == ng or ng in np
```

- [ ] **Step 5: 跑测试，确认 PASS**

Run: `python -m pytest gaia_twinkle/tests/test_scorer.py -v`
Expected: `7 passed`

- [ ] **Step 6: Commit**

```bash
git add gaia_twinkle/__init__.py gaia_twinkle/scorer.py gaia_twinkle/tests/test_scorer.py conftest.py
git commit -m "harness: scorer 模块（归一化+匹配，GAIA 近似）"
```

---

## Task 2: 样本加载 + 答案抽取

**Files:**
- Create: `gaia_twinkle/runner.py`
- Test: `gaia_twinkle/tests/test_runner.py`

- [ ] **Step 1: 写失败测试**

`gaia_twinkle/tests/test_runner.py`：
```python
import json
from pathlib import Path

from gaia_twinkle.runner import Sample, TaskResult, load_samples, extract_answer


def test_load_samples_reads_jsonl(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text(
        json.dumps({"task_id": "s1", "level": 1, "question": "q", "ground_truth": "Paris", "attachment": "a.csv"})
        + "\n"
        + json.dumps({"task_id": "s2", "question": "q2", "ground_truth": "Au"}) + "\n"
        + "# comment line\n"
        + "\n",
        encoding="utf-8",
    )
    samples = load_samples(f)
    assert len(samples) == 2
    assert samples[0].task_id == "s1"
    assert samples[0].level == 1
    assert samples[0].attachment == "a.csv"
    assert samples[1].level == 1  # default
    assert samples[1].attachment is None


def test_extract_answer_takes_last_nonempty_line():
    assert extract_answer("step 1\nstep 2\n\nParis") == "Paris"
    assert extract_answer("  Tokyo  ") == "Tokyo"
    assert extract_answer("") == ""
```

- [ ] **Step 2: 跑测试，确认 FAIL**

Run: `python -m pytest gaia_twinkle/tests/test_runner.py -v`
Expected: `ModuleNotFoundError: No module named 'gaia_twinkle.runner'`

- [ ] **Step 3: 实现 loader + extract_answer + dataclass**

`gaia_twinkle/runner.py`：
```python
"""样本加载 + 答案抽取 + 逐题执行编排。

编排：落附件进 workspace -> 构造 query -> 调 TwinkleClient -> 抽答案 -> 打分。
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Sample:
    task_id: str
    question: str
    ground_truth: str
    level: int = 1
    attachment: str | None = None
    hint: str | None = None


@dataclass
class TaskResult:
    task_id: str
    prediction: str
    ground_truth: str
    correct: bool
    error: str | None = None
    elapsed_s: float = 0.0


def load_samples(path: str | Path) -> list[Sample]:
    """读 jsonl，每行一个样本；跳过空行与 # 注释行。"""
    samples: list[Sample] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        d = json.loads(line)
        samples.append(Sample(
            task_id=d["task_id"],
            question=d["question"],
            ground_truth=d["ground_truth"],
            level=d.get("level", 1),
            attachment=d.get("attachment"),
            hint=d.get("hint"),
        ))
    return samples


def extract_answer(raw: str) -> str:
    """从 agent 原始输出抽短答案：strip；多行取最后一非空行。"""
    if not raw:
        return ""
    lines = [ln.strip() for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln]
    return lines[-1] if lines else ""
```

- [ ] **Step 4: 跑测试，确认 PASS**

Run: `python -m pytest gaia_twinkle/tests/test_runner.py -v`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add gaia_twinkle/runner.py gaia_twinkle/tests/test_runner.py
git commit -m "harness: 样本加载 + 答案抽取"
```

---

## Task 3: Twinkle WS 客户端

**Files:**
- Create: `gaia_twinkle/tests/conftest.py`
- Create: `gaia_twinkle/twinkle_client.py`
- Test: `gaia_twinkle/tests/test_twinkle_client.py`

- [ ] **Step 1: 写假 AgentServer fixture（conftest）**

`gaia_twinkle/tests/conftest.py`：
```python
import json
import pathlib
import socket
import sys

# 保证 data-sets 根在 sys.path，无论何种 pytest 调用方式。
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pytest
from websockets.asyncio.server import serve


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def free_port():
    return _free_port()


@pytest.fixture
def make_fake_agentserver():
    """工厂：传入"应答帧序列"，返回 (port, 收到的 envelope 列表, server)。

    用法：port, received, server = await make_fake_agentserver(frames)
    frames: list[dict]，收到 client envelope 后依次发送。
    """

    async def _factory(frames):
        port = _free_port()
        received: list[dict] = []

        async def handler(ws):
            # 先发 connection.ack（twinkle AgentServer 行为）
            await ws.send(json.dumps({
                "type": "event", "event": "connection.ack", "payload": {"status": "ready"}
            }))
            received.append(json.loads(await ws.recv()))  # 收 client 发来的 envelope
            for fr in frames:
                await ws.send(json.dumps(fr, ensure_ascii=False))

        server = await serve(handler, "127.0.0.1", port)
        return port, received, server

    return _factory
```

- [ ] **Step 2: 写失败测试**

`gaia_twinkle/tests/test_twinkle_client.py`：
```python
import asyncio
import json

from gaia_twinkle.twinkle_client import TwinkleClient, TwinkleError


def _frame(kind, content="", error=""):
    body = {"result": {"content": content}} if kind == "e2a.complete" else (
        {"error": error} if kind == "e2a.error" else {"result": {"content": content}}
    )
    return {
        "protocol_version": "1.0", "request_id": "r", "sequence": 0,
        "is_final": kind in ("e2a.complete", "e2a.error"),
        "status": "succeeded" if kind == "e2a.complete" else "in_progress",
        "response_kind": kind, "body": body, "is_stream": True,
    }


def test_ask_returns_complete_content(make_fake_agentserver):
    async def run():
        port, received, server = await make_fake_agentserver([_frame("e2a.complete", "Paris")])
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            ans = await client.ask("capital of France?", session_id="s1")
            assert ans == "Paris"
            assert received[0]["method"] == "chat.send"
            assert received[0]["params"]["query"] == "capital of France?"
            assert received[0]["session_id"] == "s1"
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_accumulates_chunks(make_fake_agentserver):
    async def run():
        frames = [_frame("e2a.chunk", "Par"), _frame("e2a.chunk", "is"),
                  _frame("e2a.complete", "Paris")]
        port, _, server = await make_fake_agentserver(frames)
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            ans = await client.ask("q")
            assert ans == "Paris"
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_raises_on_error(make_fake_agentserver):
    async def run():
        port, _, server = await make_fake_agentserver([_frame("e2a.error", error="boom")])
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            try:
                await client.ask("q")
            except TwinkleError as e:
                assert "boom" in str(e)
            else:
                raise AssertionError("expected TwinkleError")
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_raises_on_approval_ask(make_fake_agentserver):
    async def run():
        port, _, server = await make_fake_agentserver([_frame("e2a.ask")])
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            try:
                await client.ask("q")
            except TwinkleError as e:
                assert "approval" in str(e).lower() or "ask" in str(e).lower()
            else:
                raise AssertionError("expected TwinkleError on e2a.ask")
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_raises_on_refused_connection():
    async def run():
        client = TwinkleClient("ws://127.0.0.1:1", timeout=2)  # 端口 1 基本必拒
        try:
            await client.ask("q")
        except (TwinkleError, ConnectionError, OSError):
            return
        raise AssertionError("expected connection failure")
    asyncio.run(run())
```

- [ ] **Step 3: 跑测试，确认 FAIL**

Run: `python -m pytest gaia_twinkle/tests/test_twinkle_client.py -v`
Expected: `ModuleNotFoundError: No module named 'gaia_twinkle.twinkle_client'`

- [ ] **Step 4: 实现 TwinkleClient**

`gaia_twinkle/twinkle_client.py`：
```python
"""WS 客户端：手搓 E2A 信封直连 twinkle AgentServer。

发 E2AEnvelope(method="chat.send", params={"query":...})，读帧到 e2a.complete，
返回 body.result.content。镜像 twinkle/tests/test_agentserver_handler.py 的连接范式。
不 import twinkle。
"""
from __future__ import annotations

import asyncio
import json
import uuid

from websockets.asyncio.client import connect

PROTOCOL_VERSION = "1.0"


class TwinkleError(Exception):
    """AgentServer 返回 e2a.error / e2a.ask，或连接失败。"""


class TwinkleClient:
    def __init__(self, url: str = "ws://127.0.0.1:18000", timeout: float = 300.0):
        self.url = url
        self.timeout = timeout

    async def ask(self, query: str, session_id: str | None = None) -> str:
        """发一条 query，流式读到 final，返回答案文本。"""
        request_id = uuid.uuid4().hex
        envelope = {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "channel": "web",
            "session_id": session_id or request_id,
            "method": "chat.send",
            "params": {"query": query},
            "timestamp": 0.0,
        }
        text = ""
        try:
            async with connect(self.url) as ws:
                await ws.recv()  # connection.ack
                await ws.send(json.dumps(envelope, ensure_ascii=False))
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                    frame = json.loads(raw)
                    kind = frame.get("response_kind")
                    body = frame.get("body") or {}
                    if kind == "e2a.chunk":
                        text += (body.get("result") or {}).get("content", "") or ""
                    elif kind == "e2a.complete":
                        final = (body.get("result") or {}).get("content", "")
                        return final or text
                    elif kind == "e2a.error":
                        raise TwinkleError(body.get("error", "unknown error"))
                    elif kind == "e2a.ask":
                        raise TwinkleError(
                            "agent requested approval (e2a.ask); unattended mode cannot respond — "
                            "check twinkle permissions.enabled=false"
                        )
                    # 其余帧（todo_update 等）忽略
        except TwinkleError:
            raise
        except Exception as exc:
            raise TwinkleError(f"twinkle connection/run failed: {exc}") from exc
```

- [ ] **Step 5: 跑测试，确认 PASS**

Run: `python -m pytest gaia_twinkle/tests/test_twinkle_client.py -v`
Expected: `5 passed`

- [ ] **Step 6: Commit**

```bash
git add gaia_twinkle/twinkle_client.py gaia_twinkle/tests/conftest.py gaia_twinkle/tests/test_twinkle_client.py
git commit -m "harness: Twinkle WS 客户端（E2A 信封，含假 AgentServer fixture）"
```

---

## Task 4: 逐题执行器 run_task / run_all

**Files:**
- Modify: `gaia_twinkle/runner.py`
- Test: `gaia_twinkle/tests/test_runner.py`

- [ ] **Step 1: 追加失败测试**

在 `gaia_twinkle/tests/test_runner.py` 末尾追加：
```python
import asyncio
from gaia_twinkle.runner import run_task


class _StubClient:
    """假 client：按预设返回；记下收到的 query。"""
    def __init__(self, returns="Paris", raises=None):
        self.returns = returns
        self.raises = raises
        self.queries = []

    async def ask(self, query, session_id=None):
        self.queries.append(query)
        if self.raises:
            raise self.raises
        return self.returns


def test_run_task_copies_attachment_and_scores(tmp_path):
    work = tmp_path / "ws"
    work.mkdir()
    attach = tmp_path / "att"
    attach.mkdir()
    (attach / "capitals.csv").write_text("country,capital\nJapan,Tokyo\n", encoding="utf-8")

    sample = Sample("s4", "capital of Japan per file?", "Tokyo", attachment="capitals.csv")
    client = _StubClient(returns="Tokyo")
    result = asyncio.run(run_task(sample, client, str(work), str(attach), timeout=5))

    assert result.correct is True
    assert result.prediction == "Tokyo"
    assert (work / "capitals.csv").exists()  # 附件已落入 workspace
    # query 含文件名提示 + 答案格式约束
    assert "capitals.csv" in client.queries[0]
    assert "只输出最终答案" in client.queries[0]


def test_run_task_wrong_answer_marked_wrong():
    sample = Sample("s1", "q", "Paris")
    client = _StubClient(returns="London")
    result = asyncio.run(run_task(sample, client, "/tmp/none", "/tmp/none", timeout=5))
    assert result.correct is False
    assert result.prediction == "London"


def test_run_task_records_error(tmp_path):
    from gaia_twinkle.twinkle_client import TwinkleError
    sample = Sample("s1", "q", "Paris")
    client = _StubClient(raises=TwinkleError("boom"))
    result = asyncio.run(run_task(sample, client, str(tmp_path), str(tmp_path), timeout=5))
    assert result.correct is False
    assert "boom" in (result.error or "")
```

- [ ] **Step 2: 跑测试，确认 FAIL**

Run: `python -m pytest gaia_twinkle/tests/test_runner.py -v`
Expected: `ImportError: cannot import name 'run_task' from 'gaia_twinkle.runner'`（或类似）

- [ ] **Step 3: 实现 run_task / run_all**

在 `gaia_twinkle/runner.py` 顶部 import 区追加：
```python
import asyncio
import time

from gaia_twinkle.scorer import score
```
末尾追加：
```python
def _build_query(sample: Sample) -> str:
    q = sample.question.strip()
    if sample.attachment:
        q += f"\n\n文件 '{sample.attachment}' 已放入你的 workspace，可用 read_file 或 command_exec 查看。"
    if sample.hint:
        q += f"\n\n提示：{sample.hint}"
    q += "\n\n只输出最终答案，不要解释。"
    return q


async def run_task(
    sample: Sample,
    client,
    workspace_dir: str,
    attachments_dir: str,
    timeout: float,
) -> TaskResult:
    """跑一题：落附件 -> 构造 query -> 调 client -> 抽答案 -> 打分。"""
    start = time.monotonic()
    if sample.attachment:
        src = Path(attachments_dir) / sample.attachment
        dst = Path(workspace_dir) / sample.attachment
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    query = _build_query(sample)
    try:
        raw = await asyncio.wait_for(client.ask(query, session_id=sample.task_id), timeout=timeout)
        pred = extract_answer(raw)
        ok = score(pred, sample.ground_truth)
        return TaskResult(
            task_id=sample.task_id, prediction=pred,
            ground_truth=sample.ground_truth, correct=ok,
            elapsed_s=time.monotonic() - start,
        )
    except Exception as exc:
        return TaskResult(
            task_id=sample.task_id, prediction="",
            ground_truth=sample.ground_truth, correct=False,
            error=str(exc), elapsed_s=time.monotonic() - start,
        )


async def run_all(
    samples: list[Sample],
    client,
    workspace_dir: str,
    attachments_dir: str,
    timeout: float,
    on_result=None,
) -> list[TaskResult]:
    """顺序跑全部样本；每题完成调 on_result(result)（可选回调）。"""
    results: list[TaskResult] = []
    for s in samples:
        r = await run_task(s, client, workspace_dir, attachments_dir, timeout)
        results.append(r)
        if on_result:
            on_result(r)
    return results
```

- [ ] **Step 4: 跑测试，确认 PASS**

Run: `python -m pytest gaia_twinkle/tests/test_runner.py -v`
Expected: `5 passed`（含 Task 2 的 2 条）

- [ ] **Step 5: Commit**

```bash
git add gaia_twinkle/runner.py gaia_twinkle/tests/test_runner.py
git commit -m "harness: run_task/run_all（落附件→发问→抽答案→打分）"
```

---

## Task 5: Reporter

**Files:**
- Create: `gaia_twinkle/reporter.py`
- Test: `gaia_twinkle/tests/test_reporter.py`

- [ ] **Step 1: 写失败测试**

`gaia_twinkle/tests/test_reporter.py`：
```python
import json
from dataclasses import dataclass

from gaia_twinkle.reporter import write_report


@dataclass
class R:
    task_id: str
    prediction: str
    ground_truth: str
    correct: bool
    error: str | None = None
    elapsed_s: float = 0.0


def test_write_report_outputs_files_and_summary(tmp_path):
    results = [
        R("s1", "Paris", "Paris", True),
        R("s2", "London", "Au", False, error="timeout"),
    ]
    summary = write_report(results, str(tmp_path))
    assert summary == {"total": 2, "correct": 1, "accuracy": 0.5}

    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "results.jsonl").exists()
    assert (tmp_path / "summary.txt").exists()

    sj = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert sj["accuracy"] == 0.5

    lines = (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["task_id"] == "s1"
```

- [ ] **Step 2: 跑测试，确认 FAIL**

Run: `python -m pytest gaia_twinkle/tests/test_reporter.py -v`
Expected: `ModuleNotFoundError: No module named 'gaia_twinkle.reporter'`

- [ ] **Step 3: 实现 reporter**

`gaia_twinkle/reporter.py`：
```python
"""把逐题结果写成 results.jsonl / summary.json / summary.txt。"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _to_dict(r) -> dict:
    return asdict(r) if is_dataclass(r) else dict(r)


def write_report(results: list, output_dir: str) -> dict:
    """写报告，返回 summary dict {total, correct, accuracy}。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    total = len(results)
    correct = sum(1 for r in results if getattr(r, "correct", False))
    accuracy = (correct / total) if total else 0.0
    summary = {"total": total, "correct": correct, "accuracy": accuracy}

    (out / "results.jsonl").write_text(
        "\n".join(json.dumps(_to_dict(r), ensure_ascii=False) for r in results) + ("\n" if results else ""),
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    header = f"{'task_id':<12}{'ok':<5}{'pred':<30}{'gold':<30}error"
    rows = []
    for r in results:
        d = _to_dict(r)
        rows.append(
            f"{str(d.get('task_id','')):<12}"
            f"{str(d.get('correct')):<5}"
            f"{str(d.get('prediction',''))[:28]:<30}"
            f"{str(d.get('ground_truth',''))[:28]:<30}"
            f"{d.get('error') or ''}"
        )
    body = "\n".join(rows)
    footer = f"\naccuracy: {correct}/{total} = {accuracy:.1%}"
    (out / "summary.txt").write_text(header + "\n" + body + footer, encoding="utf-8")

    return summary
```

- [ ] **Step 4: 跑测试，确认 PASS**

Run: `python -m pytest gaia_twinkle/tests/test_reporter.py -v`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add gaia_twinkle/reporter.py gaia_twinkle/tests/test_reporter.py
git commit -m "harness: reporter（results.jsonl + summary.json + summary.txt）"
```

---

## Task 6: 样本数据 + README + .gitignore

**Files:**
- Create: `gaia_twinkle/samples/mini_gaia.jsonl`
- Create: `gaia_twinkle/samples/attachments/capitals.csv`
- Create: `gaia_twinkle/samples/attachments/sales.csv`
- Create: `gaia_twinkle/.gitignore`
- Create: `gaia_twinkle/README.md`

- [ ] **Step 1: 写样本 jsonl**

`gaia_twinkle/samples/mini_gaia.jsonl`：
```json
{"task_id":"s1","level":1,"question":"In what year was the Eiffel Tower completed?","ground_truth":"1889"}
{"task_id":"s2","level":1,"question":"Who wrote the novel 'One Hundred Years of Solitude'?","ground_truth":"Gabriel García Márquez"}
{"task_id":"s3","level":1,"question":"What is the chemical symbol for the element gold?","ground_truth":"Au"}
{"task_id":"s4","level":1,"question":"According to the file capitals.csv in your workspace, what is the capital of Japan?","ground_truth":"Tokyo","attachment":"capitals.csv"}
{"task_id":"s5","level":2,"question":"In the file sales.csv in your workspace, what is the total of the sales column?","ground_truth":"450","attachment":"sales.csv"}
{"task_id":"s6","level":2,"question":"How many letters are in the capital of France? Answer with just the number.","ground_truth":"5"}
```

- [ ] **Step 2: 写附件**

`gaia_twinkle/samples/attachments/capitals.csv`：
```csv
country,capital
Japan,Tokyo
France,Paris
Brazil,Brasilia
Canada,Ottawa
```

`gaia_twinkle/samples/attachments/sales.csv`：
```csv
month,sales
Jan,100
Feb,150
Mar,200
```

- [ ] **Step 3: 写 .gitignore**

`gaia_twinkle/.gitignore`：
```
output/
__pycache__/
*.pyc
```

- [ ] **Step 4: 写 README**

`gaia_twinkle/README.md`：
```markdown
# GAIA → Twinkle 评测 Harness（基础版）

用本地 mini 样本驱动 twinkle agent 答题，归一化精确匹配打分，产出准确率报告。
设计 spec：`docs/superpowers/specs/2026-07-30-gaia-twinkle-harness-design.md`。

## 前置

1. twinkle AgentServer 跑在 `ws://127.0.0.1:18000`（`python -m twinkle.agentserver`）。
2. twinkle `.env` 配好 `TWINKLE_LLM_API_KEY`。
3. 用 twinkle 的 venv（已含 `websockets`+`pytest`，无需装依赖）：
   ```bash
   . D:/code/opensource/github/twinkle/.venv/Scripts/activate
   ```

## 跑测试

```bash
python -m pytest gaia_twinkle/tests -v
```

## 跑评测

```bash
python -m gaia_twinkle.run_gaia \
  --agentserver-url ws://127.0.0.1:18000 \
  --workspace-dir ~/.twinkle \
  --samples gaia_twinkle/samples/mini_gaia.jsonl \
  --per-task-timeout 300
```

结果写到 `gaia_twinkle/output/<timestamp>/`（`results.jsonl` + `summary.json` + `summary.txt`）。

## 接真 GAIA（后续）

换 `runner.load_samples` 为读真实 GAIA validation 的 loader（需 HF token + 授权）；
按官方脚本对齐 `scorer`。见 spec §16。
```

- [ ] **Step 5: 验证样本可加载**

Run: `python -c "from gaia_twinkle.runner import load_samples; s=load_samples('gaia_twinkle/samples/mini_gaia.jsonl'); print(len(s), [x.task_id for x in s])"`
Expected: `6 ['s1', 's2', 's3', 's4', 's5', 's6']`

- [ ] **Step 6: Commit**

```bash
git add gaia_twinkle/samples gaia_twinkle/.gitignore gaia_twinkle/README.md
git commit -m "harness: mini 样本集 + 附件 + README"
```

---

## Task 7: CLI + 端到端冒烟

**Files:**
- Create: `gaia_twinkle/run_gaia.py`
- Test: `gaia_twinkle/tests/test_run_gaia.py`

- [ ] **Step 1: 写失败测试（只测参数解析）**

`gaia_twinkle/tests/test_run_gaia.py`：
```python
from gaia_twinkle.run_gaia import build_parser


def test_defaults():
    ns = build_parser().parse_args([])
    assert ns.agentserver_url == "ws://127.0.0.1:18000"
    assert ns.samples == "gaia_twinkle/samples/mini_gaia.jsonl"
    assert ns.per_task_timeout == 300.0


def test_overrides_and_env(monkeypatch):
    monkeypatch.setenv("TWINKLE_AGENTSERVER_URL", "ws://x:1")
    monkeypatch.setenv("TWINKLE_WORKSPACE_DIR", "/tmp/ws")
    ns = build_parser().parse_args(["--samples", "x.jsonl", "--per-task-timeout", "10"])
    assert ns.agentserver_url == "ws://x:1"
    assert ns.workspace_dir == "/tmp/ws"
    assert ns.per_task_timeout == 10.0
```

- [ ] **Step 2: 跑测试，确认 FAIL**

Run: `python -m pytest gaia_twinkle/tests/test_run_gaia.py -v`
Expected: `ModuleNotFoundError: No module named 'gaia_twinkle.run_gaia'`

- [ ] **Step 3: 实现 CLI**

`gaia_twinkle/run_gaia.py`：
```python
"""CLI：加载样本 -> 连 twinkle -> 逐题跑 -> 打分 -> 写报告。"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import os
import sys
from pathlib import Path

from gaia_twinkle.reporter import write_report
from gaia_twinkle.runner import load_samples, run_all
from gaia_twinkle.twinkle_client import TwinkleClient


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GAIA-style eval harness for twinkle.")
    p.add_argument("--agentserver-url", default=os.environ.get(
        "TWINKLE_AGENTSERVER_URL", "ws://127.0.0.1:18000"))
    p.add_argument("--workspace-dir", default=os.environ.get(
        "TWINKLE_WORKSPACE_DIR", str(Path.home() / ".twinkle")))
    p.add_argument("--samples", default="gaia_twinkle/samples/mini_gaia.jsonl")
    p.add_argument("--attachments-dir", default="gaia_twinkle/samples/attachments")
    p.add_argument("--per-task-timeout", type=float, default=300.0)
    p.add_argument("--output", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    samples = load_samples(args.samples)
    if not samples:
        print(f"no samples loaded from {args.samples}", file=sys.stderr)
        return 2

    client = TwinkleClient(args.agentserver_url, timeout=args.per_task_timeout)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = args.output or f"gaia_twinkle/output/{ts}"

    def on_result(r) -> None:
        flag = "✓" if r.correct else "✗"
        print(f"[{flag}] {r.task_id}: pred={r.prediction!r} gold={r.ground_truth!r} "
              f"{r.error or ''}")

    Path(args.workspace_dir).mkdir(parents=True, exist_ok=True)
    results = asyncio.run(run_all(
        samples, client, args.workspace_dir, args.attachments_dir,
        args.per_task_timeout, on_result,
    ))

    summary = write_report(results, out_dir)
    print(f"\naccuracy: {summary['correct']}/{summary['total']} = {summary['accuracy']:.1%}")
    print(f"report: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试，确认 PASS**

Run: `python -m pytest gaia_twinkle/tests/test_run_gaia.py -v`
Expected: `2 passed`

- [ ] **Step 5: 跑全量测试**

Run: `python -m pytest gaia_twinkle/tests -v`
Expected: 全部 PASS（scorer 7 + runner 5 + twinkle_client 5 + reporter 1 + run_gaia 2 = 20 passed）

- [ ] **Step 6: Commit**

```bash
git add gaia_twinkle/run_gaia.py gaia_twinkle/tests/test_run_gaia.py
git commit -m "harness: CLI run_gaia + 参数解析测试"
```

- [ ] **Step 7: 端到端冒烟（手动，需 twinkle 跑着）**

前置确认：twinkle AgentServer 起在 :18000 且 `.env` 有 `TWINKLE_LLM_API_KEY`：
```bash
. D:/code/opensource/github/twinkle/.venv/Scripts/activate   # 另一终端跑 twinkle
python -m twinkle.agentserver
```

跑 harness（data-sets 根目录）：
```bash
python -m gaia_twinkle.run_gaia --samples gaia_twinkle/samples/mini_gaia.jsonl --per-task-timeout 300
```
Expected：逐题打印 `[✓]/[✗] sN: pred=... gold=...`；末尾打印 `accuracy: X/6 = ...`；`gaia_twinkle/output/<ts>/` 下三文件齐备。

- [ ] **Step 8: Commit 冒烟产物（可选）**

```bash
# 产物在 .gitignore 里，默认不提交。如想留一份基线：
git add -f gaia_twinkle/output/<ts>/summary.json
git commit -m "harness: 首次端到端冒烟基线"
```

---

## Self-Review（写完后自查，已修正）

1. **Spec 覆盖**：§5 组件 → Task1 scorer / Task3 client / Task2+4 runner / Task5 reporter / Task7 CLI 全覆盖；§7 样本 schema → Task6；§8 附件 → Task4 run_task 落件 + Task6 附件；§9 答案抽取 → Task2 extract_answer；§10 打分 → Task1；§11 CLI → Task7；§12 错误 → Task3(TwinkleError/ask/error) + Task4(error 记录)；§13 测试 → 各 Task；§15 验收 → Task7 Step5+Step7。无遗漏。
2. **占位符扫描**：无 TBD/TODO；每步有实码。
3. **类型/命名一致**：`normalize/score`（T1）→ T4 引用一致；`TwinkleClient.ask(query, session_id=None)`（T3）→ T4 `_StubClient.ask` 同签名；`Sample`/`TaskResult`（T2）→ T4/T5 一致；`run_task(sample, client, workspace_dir, attachments_dir, timeout)`（T4）→ T7 `run_all(...)` 调用一致；`write_report(results, output_dir)`（T5）→ T7 一致。
4. **已知风险**：§10 子串误匹配（金标 "1" 匹配 "100"）已在 scorer docstring 与 spec §10 标注，首版接受。
