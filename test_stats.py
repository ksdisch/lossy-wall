"""test_stats.py — offline unit tests for the proportion CIs (ported from decay-pin).

No network, no model. decay-pin ran these as a hand-rolled `uv run test_stats.py` script;
lossy-wall standardizes on pytest (`uv run pytest`) so ONE command greens the whole repo
before any paid call. The conversion is also a trap removal: a `test_*.py` file whose
test functions print-and-collect instead of asserting would "pass" vacuously under pytest
— every check here now asserts. Reference values are decay-pin's, unchanged
(hand-computed, 95%, z = 1.96), plus two lossy-wall-specific shapes: the wall (claim 1)
and the D7 equivalence arithmetic (claim 2).

These intervals are the project's *ruler*: if the math is off, every wall / equivalence /
worse-than-empty claim downstream is wrong.
"""
from __future__ import annotations

from stats import excludes_zero, newcombe_diff, wilson


def close(a: float, b: float, tol: float = 5e-4) -> bool:
    return abs(a - b) <= tol


def test_wilson_known_values():
    # p = 0.5, n = 20 -> symmetric around 0.5, ~(0.299, 0.701)
    lo, hi = wilson(10, 20)
    assert close(lo, 0.2993)
    assert close(hi, 0.7007)
    assert close((lo + hi) / 2, 0.5)

    # p = 0.8, n = 20 -> ~(0.584, 0.919)
    lo, hi = wilson(16, 20)
    assert close(lo, 0.5840)
    assert close(hi, 0.9193)


def test_wilson_edges():
    # k=0 is where our lossy wall cells live: upper ~16% at n=20 —
    # "consistent with ~0%", never "proved 0%".
    lo, hi = wilson(0, 20)
    assert lo == 0.0
    assert close(hi, 0.1611)

    lo, hi = wilson(20, 20)
    assert hi == 1.0
    assert close(lo, 0.8389)

    lo, hi = wilson(0, 0)
    assert lo == 0.0 and hi == 1.0

    for k, n in [(0, 5), (3, 5), (5, 5), (7, 13), (40, 40)]:
        lo, hi = wilson(k, n)
        assert 0.0 <= lo <= hi <= 1.0


def test_wilson_d7_wall_cell():
    # The D7 fact the escalation rule stands on: a clean 0/40 has Wilson upper ~0.0876,
    # so a clean pair of 0/40 cells fits inside the δ=0.10 equivalence band.
    lo, hi = wilson(0, 40)
    assert lo == 0.0
    assert close(hi, 0.0876)


def test_newcombe_overlap_case():
    # A mild gap (16/20 vs 20/20) straddles 0 -> "not a result".
    d, lo, hi = newcombe_diff(16, 20, 20, 20)  # 80% vs 100%
    assert close(d, 0.20)
    assert close(lo, -0.0005)
    assert close(hi, 0.4160)
    assert excludes_zero(lo, hi) is False


def test_newcombe_clear_case():
    # A crisp gap (24/40 vs 38/40) excludes 0 -> a real result.
    d, lo, hi = newcombe_diff(24, 40, 38, 40)  # 60% vs 95%
    assert close(d, 0.35)
    assert close(lo, 0.171, tol=2e-3)
    assert close(hi, 0.508, tol=2e-3)
    assert excludes_zero(lo, hi) is True


def test_newcombe_wall_shape():
    # The shape M1 hopes to see at the wall (paper: lossy RR 0.00 vs source_first
    # 0.99–1.00): base=lossy 0/20, mech=source_first 20/20.
    d, lo, hi = newcombe_diff(0, 20, 20, 20)
    assert close(d, 1.0)
    assert lo > 0.0 and excludes_zero(lo, hi) is True
    assert -1.0 <= lo <= hi <= 1.0


def test_newcombe_d7_equivalence_shape():
    # Claim 2's arithmetic (D7): a clean pair (0/40 vs 0/40) sits entirely inside the
    # ±0.10 band — decidable. A single stray reclaim (0/40 vs 1/40) pushes the upper
    # bound to ~0.129, busting the band — which is exactly why the escalation rule
    # (extend to N≈90) was pre-committed.
    d, lo, hi = newcombe_diff(0, 40, 0, 40)
    assert close(d, 0.0)
    assert -0.10 < lo and hi < 0.10

    d, lo, hi = newcombe_diff(0, 40, 1, 40)
    assert close(hi, 0.1288, tol=2e-3)
    assert not (hi < 0.10)


def test_excludes_zero_logic():
    assert excludes_zero(0.1, 0.4) is True
    assert excludes_zero(-0.4, -0.1) is True   # a real *negative* effect still excludes 0
    assert excludes_zero(-0.05, 0.30) is False
    assert excludes_zero(0.0, 0.30) is False   # touching 0 is NOT a clear result
