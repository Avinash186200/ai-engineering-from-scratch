import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_stats import gate_decision, paired_compare, wilson_interval  # noqa: E402


def test_perfect_small_sample_is_not_certain():
    low, high = wilson_interval(10, 10)
    assert high == 1.0
    assert 0.65 < low < 0.75


def test_interval_narrows_with_more_cases():
    w_small = wilson_interval(9, 10)
    w_big = wilson_interval(90, 100)
    assert (w_big[1] - w_big[0]) < (w_small[1] - w_small[0])


@pytest.mark.parametrize("passed,total", [(0, 5), (3, 7), (50, 50)])
def test_interval_contains_point_estimate(passed, total):
    low, high = wilson_interval(passed, total)
    assert low <= passed / total <= high


def test_bad_inputs_raise():
    with pytest.raises(ValueError):
        wilson_interval(1, 0)
    with pytest.raises(ValueError):
        wilson_interval(6, 5)
    with pytest.raises(ValueError):
        paired_compare([True], [True, False])


def test_identical_runs_show_no_difference():
    runs = [True, False, True]
    c = paired_compare(runs, runs)
    assert c.p_value == 1.0 and c.verdict == "no clear difference"


def test_small_disagreement_is_noise():
    a = [True, True, False, True]
    b = [True, False, True, True]
    assert paired_compare(a, b).verdict == "no clear difference"


def test_gate_three_outcomes():
    assert gate_decision(200, 200) == "pass"
    assert gate_decision(5, 10) == "fail"
    assert gate_decision(9, 10) == "unsure"
