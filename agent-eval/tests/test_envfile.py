"""envfile 加载器测试：纯逻辑 + os.environ 应用语义。

优先级：CLI flag > 已有 shell 环境变量 > .env 文件 > 默认。
所以 apply_env 默认只补「缺失」的键，不覆盖已存在的。
"""

import os

from evalbench.envfile import apply_env, load_env_file, parse_env_text


# ---- parse_env_text（纯函数）----

def test_parse_basic_key_value():
    assert parse_env_text("OPENAI_API_KEY=sk-123\n") == {"OPENAI_API_KEY": "sk-123"}


def test_parse_skips_comments_and_blanks():
    text = "# 这是注释\n\nOPENAI_MODEL_NAME=gpt-4o-mini\n   # 缩进注释\n"
    assert parse_env_text(text) == {"OPENAI_MODEL_NAME": "gpt-4o-mini"}


def test_parse_strips_surrounding_whitespace_and_quotes():
    text = 'KEY1 = "value with spaces"  \nKEY2=\'val\'\nKEY3 = plain \n'
    assert parse_env_text(text) == {
        "KEY1": "value with spaces",
        "KEY2": "val",
        "KEY3": "plain",
    }


def test_parse_empty_value():
    assert parse_env_text("EMPTY=\n") == {"EMPTY": ""}


def test_parse_skips_lines_without_equals():
    text = "NO_EQUALS_HERE\nKEY=val\n"
    assert parse_env_text(text) == {"KEY": "val"}


def test_parse_inline_hash_is_part_of_value():
    # 行内 # 不当注释剥（值里可能真含 #），只认行首 #
    assert parse_env_text("KEY=val # not stripped\n") == {"KEY": "val # not stripped"}


# ---- load_env_file ----

def test_load_missing_file_returns_empty(tmp_path):
    assert load_env_file(tmp_path / "nope.env") == {}


def test_load_real_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("OPENAI_API_KEY=sk-x\n# c\nMODEL=y\n", encoding="utf-8")
    assert load_env_file(p) == {"OPENAI_API_KEY": "sk-x", "MODEL": "y"}


# ---- apply_env（os.environ 语义）----

_PREFIX = "REL_EVAL_TEST_"


def _cleanup(*keys):
    for k in keys:
        os.environ.pop(k, None)


def test_apply_env_only_fills_missing_keys():
    a, b, c = _PREFIX + "A", _PREFIX + "B", _PREFIX + "C"
    _cleanup(a, b, c)
    os.environ[a] = "from-shell"  # 已存在
    try:
        set_keys = apply_env({a: "from-file", b: "from-file"})
        assert os.environ[a] == "from-shell"  # shell 赢，不被覆盖
        assert os.environ[b] == "from-file"   # 缺失才补
        assert set_keys == [b]
    finally:
        _cleanup(a, b, c)


def test_apply_env_overwrite_replaces_existing():
    a = _PREFIX + "OW"
    _cleanup(a)
    os.environ[a] = "old"
    try:
        apply_env({a: "new"}, overwrite=True)
        assert os.environ[a] == "new"
    finally:
        _cleanup(a)
