"""Presentation regression contract for the documented UI example."""

import pytest

from core.engine_2x2 import Table2x2, analyze_2x2
from ui.formatting import fmt_ci, fmt_num, fmt_p


def test_default_example_snapshot_contract():
    result = analyze_2x2(Table2x2(25, 15, 7, 30), alpha=0.05)
    snapshot = {
        "RR": (fmt_num(result["risk_ratio"]), fmt_ci(result["risk_ratio_katz_ci"])),
        "OR": (fmt_num(result["odds_ratio"]), fmt_ci(result["odds_ratio_woolf_ci"])),
        "RD": (fmt_num(result["risk_difference"]), fmt_ci(result["risk_difference_wald_ci"], 3)),
        "Pearson": fmt_num(result["pearson_chi2"]),
        "Fisher": fmt_p(result["fisher_two_sided_p"]),
    }
    assert snapshot == {
        "RR": ("3.30", "1.63 – 6.71"),
        "OR": ("7.14", "2.52 – 20.26"),
        "RD": ("0.436", "0.240 – 0.632"),
        "Pearson": "15.03",
        "Fisher": "p < 0.001",
    }
    assert result["risk_ratio"] == pytest.approx(3.30, abs=0.01)
    assert result["risk_ratio_katz_ci"] == pytest.approx((1.63, 6.71), abs=0.01)
    assert result["odds_ratio"] == pytest.approx(7.14, abs=0.01)
    assert result["odds_ratio_woolf_ci"] == pytest.approx((2.52, 20.26), abs=0.01)
    assert result["risk_difference"] == pytest.approx(0.436, abs=0.001)
    assert result["risk_difference_wald_ci"] == pytest.approx((0.240, 0.632), abs=0.001)
    assert result["pearson_chi2"] == pytest.approx(15.03, abs=0.01)
    assert result["fisher_two_sided_p"] == pytest.approx(0.00017, abs=0.00001)

