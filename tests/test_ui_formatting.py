import pytest

from ui.formatting import fmt_ci, fmt_num, fmt_pct, fmt_p


@pytest.mark.parametrize(("value", "expected"), [
    (None, "—"), (float("nan"), "—"), (0, "0"),
    (0.1891891891891892, "0.189"), (3.3035714285714284, "3.30"),
    (123456, "1.23e+05"),
])
def test_fmt_num(value, expected):
    assert fmt_num(value) == expected


@pytest.mark.parametrize(("value", "expected"), [
    (0.00010576332579574142, "p < 0.001"),
    (0.000999, "p < 0.001"), (0.001, "0.001"),
    (0.049876, "0.0499"), (1, "1"), (None, "—"),
])
def test_fmt_p(value, expected):
    assert fmt_p(value) == expected


def test_fmt_ci_and_undefined_intervals():
    assert fmt_ci((1.625924, 6.712234)) == "1.63 – 6.71"
    assert fmt_ci(None) == "Not estimable"
    assert fmt_ci((0, float("inf"))) == "Not estimable"


def test_fmt_pct():
    assert fmt_pct(0.625) == "62.5%"
    assert fmt_pct(0.697) == "69.7%"
    assert fmt_pct(None) == "—"

