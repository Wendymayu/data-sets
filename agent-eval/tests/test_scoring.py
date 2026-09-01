"""纯逻辑测试：不涉及 LLM、不涉及网络。

用手搓的 SampleResult 列表验证预测/准确率/混淆矩阵/P/R/F1/按样本类型分组。
"""

from evalbench.scoring import (
    ConfusionMatrix,
    Metrics,
    SampleResult,
)


def _fx(threshold: float = 0.5) -> list[SampleResult]:
    """7 条样本，覆盖正/强负/难负三类型 + 一条 errored。

    记分卡 (threshold=0.5):
      p1  positive label1 score0.9 -> pred1 correct (tp)
      p2  positive label1 score0.4 -> pred0 wrong  (fn)
      p3  positive label1 score None -> errored (no pred, wrong)
      s1  strong  label0 score0.1 -> pred0 correct (tn)
      s2  strong  label0 score0.8 -> pred1 wrong  (fp)
      h1  hard    label0 score0.55-> pred1 wrong  (fp, 难负命中失败)
      h2  hard    label0 score0.2 -> pred0 correct (tn)
    => n_total=7 n_judged=6 n_errored=1 n_correct=3 accuracy=3/7≈0.4286
       混淆(判过6条): tp1 fp2 fn1 tn2 -> P=1/3 R=1/2 F1=0.4
       正3 acc1/3 ; 强2 acc1/2 ; 难2 acc1/2
    """
    return [
        SampleResult("p1", "i1", "o1", 1, "positive", 0.9, threshold=threshold),
        SampleResult("p2", "i2", "o2", 1, "positive", 0.4, threshold=threshold),
        SampleResult("p3", "i3", "o3", 1, "positive", None, threshold=threshold),
        SampleResult("s1", "i4", "o4", 0, "strong_negative", 0.1, threshold=threshold),
        SampleResult("s2", "i5", "o5", 0, "strong_negative", 0.8, threshold=threshold),
        SampleResult("h1", "i6", "o6", 0, "hard_negative", 0.55, threshold=threshold),
        SampleResult("h2", "i7", "o7", 0, "hard_negative", 0.2, threshold=threshold),
    ]


# ---------- SampleResult ----------

def test_predicted_at_threshold_boundary_is_relevant():
    # score == threshold => 相关 (>=)
    r = SampleResult("x", "i", "o", 1, "positive", 0.5, threshold=0.5)
    assert r.predicted == 1
    r2 = SampleResult("x", "i", "o", 1, "positive", 0.499, threshold=0.5)
    assert r2.predicted == 0


def test_errored_sample_has_no_prediction_and_is_wrong():
    r = SampleResult("e", "i", "o", 1, "positive", None, threshold=0.5, error="boom")
    assert r.predicted is None
    assert r.correct is False


def test_correct_matches_label():
    assert SampleResult("a", "i", "o", 1, "positive", 0.9, threshold=0.5).correct is True
    assert SampleResult("b", "i", "o", 0, "hard_negative", 0.1, threshold=0.5).correct is True
    assert SampleResult("c", "i", "o", 1, "positive", 0.3, threshold=0.5).correct is False
    assert SampleResult("d", "i", "o", 0, "strong_negative", 0.6, threshold=0.5).correct is False


# ---------- Metrics: counts & accuracy ----------

def test_metrics_counts_and_accuracy():
    m = Metrics(_fx())
    assert m.n_total == 7
    assert m.n_judged == 6
    assert m.n_errored == 1
    assert m.n_correct == 3
    assert m.accuracy == 3 / 7
    assert m.coverage == 6 / 7


def test_empty_metrics_does_not_crash():
    m = Metrics([])
    assert m.n_total == 0
    assert m.accuracy == 0.0
    assert m.coverage == 0.0
    assert m.confusion.total == 0
    assert m.passes_gate() is False  # 0 accuracy


# ---------- ConfusionMatrix + P/R/F1 ----------

def test_confusion_matrix_over_judged_only():
    cm = Metrics(_fx()).confusion
    # errored 样本不计入混淆矩阵
    assert (cm.tp, cm.fp, cm.fn, cm.tn) == (1, 2, 1, 2)
    assert cm.total == 6
    assert cm.accuracy == (1 + 2) / 6  # 0.5 — 与 headline accuracy(0.4286) 不同


def test_precision_recall_f1():
    m = Metrics(_fx())
    assert m.precision == 1 / 3
    assert m.recall == 1 / 2
    assert m.f1 == 0.4


def test_confusion_matrix_degenerate_precision():
    # 没有 pred=1 的预测时 precision=0 而非除零
    rs = [
        SampleResult("a", "i", "o", 0, "strong_negative", 0.1, threshold=0.5),
        SampleResult("b", "i", "o", 0, "strong_negative", 0.2, threshold=0.5),
    ]
    m = Metrics(rs)
    assert m.confusion.tp == 0 and m.confusion.fp == 0
    assert m.precision == 0.0
    assert m.recall == 0.0
    assert m.f1 == 0.0


# ---------- per sample-type breakdown ----------

def test_by_type_breakdown():
    bt = Metrics(_fx()).by_type
    assert set(bt.keys()) == {"positive", "strong_negative", "hard_negative"}
    pos, strong, hard = bt["positive"], bt["strong_negative"], bt["hard_negative"]
    assert (pos.total, pos.correct, pos.errored) == (3, 1, 1)
    assert (strong.total, strong.correct, strong.errored) == (2, 1, 0)
    assert (hard.total, hard.correct, hard.errored) == (2, 1, 0)
    assert pos.accuracy == 1 / 3
    assert strong.accuracy == 1 / 2
    assert hard.accuracy == 1 / 2
    assert pos.judged == 2  # 3 - 1 errored


# ---------- gate ----------

def test_passes_gate():
    m = Metrics(_fx())
    assert m.passes_gate(0.80) is False
    assert m.passes_gate(0.40) is True
    # 默认门限 0.80
    assert m.passes_gate() is False


def test_perfect_run_passes_gate():
    rs = [
        SampleResult("p", "i", "o", 1, "positive", 1.0, threshold=0.5),
        SampleResult("n", "i", "o", 0, "hard_negative", 0.0, threshold=0.5),
    ]
    m = Metrics(rs)
    assert m.accuracy == 1.0
    assert m.passes_gate(0.80) is True
