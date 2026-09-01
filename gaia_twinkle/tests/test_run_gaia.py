from gaia_twinkle.run_gaia import build_parser, apply_eval_set


def test_defaults():
    ns = build_parser().parse_args([])
    assert ns.agentserver_url == "ws://127.0.0.1:18000"
    assert ns.samples == "gaia_twinkle/data/smoke/tasks.jsonl"
    assert ns.attachments_dir == "gaia_twinkle/data/smoke/attachments"
    assert ns.per_task_timeout == 300.0
    assert ns.concurrency == 4
    assert ns.retries == 1  # 默认重试一次（空答案/超时题）；--retries 0 关
    assert ns.eval_set is None
    assert ns.limit is None


def test_retries_override():
    assert build_parser().parse_args(["--retries", "0"]).retries == 0
    assert build_parser().parse_args(["--retries", "3"]).retries == 3


def test_overrides_and_env(monkeypatch):
    monkeypatch.setenv("TWINKLE_AGENTSERVER_URL", "ws://x:1")
    monkeypatch.setenv("TWINKLE_WORKSPACE_DIR", "/tmp/ws")
    ns = build_parser().parse_args(["--samples", "x.jsonl", "--per-task-timeout", "10", "--limit", "3"])
    assert ns.agentserver_url == "ws://x:1"
    assert ns.workspace_dir == "/tmp/ws"
    assert ns.per_task_timeout == 10.0
    assert ns.limit == 3


def test_eval_set_overrides_paths():
    ns = build_parser().parse_args(["--eval-set", "attachments"])
    assert ns.eval_set == "attachments"
    # before apply, samples still default (smoke)
    assert ns.samples == "gaia_twinkle/data/smoke/tasks.jsonl"
    apply_eval_set(ns)
    assert ns.samples == "gaia_twinkle/data/attachments/tasks.jsonl"
    assert ns.attachments_dir == "gaia_twinkle/data/gaia/2023/validation"


def test_eval_set_hard():
    ns = build_parser().parse_args(["--eval-set", "hard"])
    apply_eval_set(ns)
    assert ns.samples == "gaia_twinkle/data/hard/tasks.jsonl"
    assert ns.attachments_dir == "gaia_twinkle/data/gaia/2023/validation"
