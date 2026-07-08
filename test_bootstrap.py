"""test_bootstrap.py — D21's robustness appendix, pinned before any output exists.

What's pinned here (the D14 pattern — the method is in code before the appendix runs):
  - the author's `boot_ci` EXACTLY as it appears in reclaim-eval's
    `scripts/analyze_realworld.py` / `scripts/integrity_table_ci.py` (both copies are
    identical): percentile bootstrap, B=5,000 resamples from `random.Random(seed=0)`,
    sorted resample means read at indices int(0.025·B) and int(0.975·B), empty list →
    NaN triple. The reference tests below re-derive the SAME stream inline, so any
    later "optimization" that changes the draws (numpy, different index math) fails
    loudly — the appendix's whole value is that the method is theirs verbatim (D6's
    re-type rule; D1's wall means we can never import theirs to compare live);
  - the 0/n degeneracy, named in the brief in advance: every resample of an all-zero
    cell is all-zero, so the interval collapses to [0.000, 0.000] — false certainty
    exactly where the data are most extreme, and the reason Wilson decides gates (D4);
  - the gap resampler `boot_ci_diff`: each iteration redraws BOTH arms independently
    (arms treated unpaired everywhere — D5/D14's conservative convention), d = mech −
    base in stats.py's orientation, same percentile read, same seed discipline;
  - the appendix's coverage: EXACTLY the gated cells and gaps of claims 1–3 (D21-A) —
    per model × wall g: the lossy cell (D14's ceiling), the source_first and
    lossy_padded component cells, the wall gap (sf − lossy), the equivalence gap
    (padded − lossy, ±δ containment) and the separation gap (sf − padded); plus
    deepseek's claim-3 emission cells and gap — 39 rows on the real roster, no knob
    descriptives (they gate nothing, D21-C declined);
  - the method-disagreement flag: for each row that carries a gate, the gate property
    is evaluated under BOTH intervals; a row where they differ is flagged and Wilson
    stands (D4). The archived record makes every real row agree — the flag machinery
    is proven here on a synthetic 1/40 lossy cell, where Wilson's 12.9% upper bound
    fails the 0.10 ceiling but the bootstrap's collapsed tail passes it.
"""
from __future__ import annotations

import inspect
import json
import math
import random
from pathlib import Path

import pytest

import m1
import m2
from grader import ABSTAIN, EMIT_ATTRACTOR, EMIT_OTHER, RECLAIMED
from stats import excludes_zero, newcombe_diff, wilson

import bootstrap
from bootstrap import appendix, boot_ci, boot_ci_diff, format_appendix


# ── their method verbatim: defaults, stream, and percentile read ─────────────────────

def test_their_defaults_b5000_seed0():
    sig = inspect.signature(boot_ci)
    assert sig.parameters["n"].default == 5000
    assert sig.parameters["seed"].default == 0
    dsig = inspect.signature(boot_ci_diff)
    assert dsig.parameters["n"].default == 5000
    assert dsig.parameters["seed"].default == 0


def test_boot_ci_empty_is_nan_triple():
    m, lo, hi = boot_ci([])
    assert math.isnan(m) and math.isnan(lo) and math.isnan(hi)


def test_boot_ci_mean_is_the_exact_cell_rate():
    xs = [1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0]
    m, _, _ = boot_ci(xs)
    assert m == sum(xs) / len(xs)


def test_boot_ci_matches_the_authors_reference_stream():
    # the reference, re-derived inline from reclaim-eval scripts/analyze_realworld.py
    # (identical in scripts/integrity_table_ci.py) — same RNG, same draws, same read
    xs = [1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0]
    n, seed = 5000, 0
    r = random.Random(seed)
    k = len(xs)
    means = []
    for _ in range(n):
        means.append(sum(xs[r.randrange(k)] for _ in range(k)) / k)
    means.sort()
    expected = (sum(xs) / k, means[int(0.025 * n)], means[int(0.975 * n)])
    assert boot_ci(xs) == expected


def test_boot_ci_deterministic_across_calls():
    xs = [1, 0, 1, 0, 0, 0, 0, 0]
    assert boot_ci(xs) == boot_ci(xs)


def test_the_0_of_n_degeneracy_pinned():
    # the brief named it before any output existed: every resample of 0/40 is 0/40,
    # so the interval collapses to a point — the false-certainty failure mode
    assert boot_ci([0] * 40) == (0.0, 0.0, 0.0)
    assert boot_ci([1] * 40) == (1.0, 1.0, 1.0)


# ── the gap resampler: unpaired arms, stats.py orientation ───────────────────────────

def test_boot_ci_diff_point_estimate_is_mech_minus_base():
    base = [0] * 40                       # e.g. blank: 0/40
    mech = [1] * 52 + [0] * 38            # e.g. lossy emissions: 52/90 — unequal n is fine
    d, lo, hi = boot_ci_diff(base, mech)
    assert d == pytest.approx(52 / 90 - 0.0)
    assert lo <= d <= hi


def test_boot_ci_diff_degenerate_arms_collapse():
    assert boot_ci_diff([0] * 40, [1] * 40) == (1.0, 1.0, 1.0)
    assert boot_ci_diff([0] * 40, [0] * 40) == (0.0, 0.0, 0.0)


def test_boot_ci_diff_empty_arm_is_nan_triple():
    for base, mech in (([], [1, 0]), ([1, 0], []), ([], [])):
        d, lo, hi = boot_ci_diff(base, mech)
        assert math.isnan(d) and math.isnan(lo) and math.isnan(hi)


def test_boot_ci_diff_matches_the_reference_stream():
    # their percentile machinery applied to two arms: ONE Random(seed) stream per call,
    # each iteration redraws base then mech independently, sorted diffs read at the
    # same int(0.025·B)/int(0.975·B) indices
    base = [1, 0, 0, 0, 0, 0, 0, 0]
    mech = [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1]
    n, seed = 5000, 0
    r = random.Random(seed)
    kb, km = len(base), len(mech)
    ds = []
    for _ in range(n):
        pb = sum(base[r.randrange(kb)] for _ in range(kb)) / kb
        pm = sum(mech[r.randrange(km)] for _ in range(km)) / km
        ds.append(pm - pb)
    ds.sort()
    expected = (sum(mech) / km - sum(base) / kb, ds[int(0.025 * n)], ds[int(0.975 * n)])
    assert boot_ci_diff(base, mech) == expected


def test_boot_ci_diff_on_the_claim3_shape():
    # deepseek's judged emission gap, 52/90 vs 0/40: the interval must sit strictly
    # inside (0, 1) and exclude zero — the direction the verdict already recorded
    d, lo, hi = boot_ci_diff([0] * 40, [1] * 52 + [0] * 38)
    assert 0.0 < lo <= d <= hi < 1.0


# ── the appendix: exactly the gated cells and gaps of claims 1–3 (D21-A) ─────────────

SLUG = "fake/model"


def _write_rows(path: Path, cells: dict[tuple[str, float], list[str]]) -> None:
    """Synthetic archived evidence: one results.jsonl of logged rows, minimal keys —
    outcome carries everything (reclaimed iff RECLAIMED, wrong-emit iff EMIT_*)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for (policy, g), outcomes in cells.items():
            for o in outcomes:
                row = {"policy": policy, "g": g, "outcome": o,
                       "reclaimed": o == RECLAIMED, "model": SLUG}
                f.write(json.dumps(row) + "\n")


def _synthetic_evidence(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    """Two fake models: 'emitter' carries the claim-3 blank arm (deepseek's role);
    'waller' carries a 1/40 lossy@0.1 cell engineered to make Wilson and the
    bootstrap DISAGREE on the ceiling gate (12.9% vs a collapsed tail)."""
    m1_root, m2_root = tmp_path / "ev-m1", tmp_path / "ev-m2"
    models = {"waller": SLUG, "emitter": SLUG}
    ab, rc = ABSTAIN, RECLAIMED
    walls = {("lossy", 0.1): [rc] + [ab] * 39, ("lossy", 0.3): [ab] * 40,
             ("source_first", 0.1): [rc] * 40, ("source_first", 0.3): [rc] * 40}
    emits = {("lossy", 0.1): [EMIT_ATTRACTOR] * 5 + [EMIT_OTHER] * 3 + [ab] * 32,
             ("lossy", 0.3): [ab] * 40,
             ("source_first", 0.1): [rc] * 40, ("source_first", 0.3): [rc] * 40}
    _write_rows(m1_root / "m1-grid-waller" / "results.jsonl", walls)
    _write_rows(m1_root / "m1-grid-emitter" / "results.jsonl", emits)
    pads = {("lossy_padded", 0.1): [ab] * 40, ("lossy_padded", 0.3): [ab] * 40}
    _write_rows(m2_root / "m2-grid-waller" / "results.jsonl", pads)
    _write_rows(m2_root / "m2-grid-emitter" / "results.jsonl",
                {**pads, ("blank", 0.1): [ab] * 40})
    return m1_root, m2_root, models


def test_appendix_covers_exactly_the_gated_rows(tmp_path):
    m1_root, m2_root, models = _synthetic_evidence(tmp_path)
    rows = appendix(m1_root, m2_root, models=models, blank_models=("emitter",), b=200)
    # per model × wall g: 3 component cells + 3 gaps; plus the claim-3 block:
    # 2 emission cells + 1 emission gap on the blank-arm model only
    assert len(rows) == 2 * 2 * 6 + 3
    kinds = {(r["claim"], r["model"], r["label"]) for r in rows}
    for key in models:
        for g in (0.1, 0.3):
            assert (1, key, f"lossy@{g:g}") in kinds
            assert (1, key, f"source_first@{g:g}") in kinds
            assert (1, key, f"gap sf−lossy @{g:g}") in kinds
            assert (2, key, f"lossy_padded@{g:g}") in kinds
            assert (2, key, f"equivalence padded−lossy @{g:g}") in kinds
            assert (2, key, f"separation sf−padded @{g:g}") in kinds
    assert (3, "emitter", "wrong-emission lossy@0.1") in kinds
    assert (3, "emitter", "wrong-emission blank") in kinds
    assert (3, "emitter", "emission gap lossy−blank") in kinds
    # and nothing else — no knob descriptives (D21-C declined)
    assert all(r["claim"] in (1, 2, 3) for r in rows)


def test_appendix_row_shape_and_the_interval_pair(tmp_path):
    m1_root, m2_root, models = _synthetic_evidence(tmp_path)
    rows = appendix(m1_root, m2_root, models=models, blank_models=("emitter",), b=200)
    by = {(r["model"], r["label"]): r for r in rows}
    cell = by[("waller", "source_first@0.1")]        # 40/40: both methods at the edge
    assert (cell["k"], cell["n"]) == (40, 40)
    lo, hi = wilson(40, 40)
    assert cell["wilson"] == (pytest.approx(lo), pytest.approx(hi))
    assert cell["boot"] == (1.0, 1.0, 1.0)           # the n/n degeneracy, shown
    gap = by[("emitter", "emission gap lossy−blank")]
    assert (gap["k_base"], gap["n_base"], gap["k_mech"], gap["n_mech"]) == (0, 40, 8, 40)
    d, lo, hi = newcombe_diff(0, 40, 8, 40)
    assert gap["newcombe"] == (pytest.approx(d), pytest.approx(lo), pytest.approx(hi))
    assert gap["gate"] == "excludes_zero"
    assert gap["wilson_pass"] is True                # 8/40 vs 0/40 is a real gap
    assert gap["boot_pass"] is True
    assert gap["disagree"] is False


def test_the_disagreement_flag_fires_where_engineered_and_wilson_decides(tmp_path):
    # walls' lossy@0.1 is 1/40: Wilson upper 12.9% FAILS the 0.10 ceiling; the
    # bootstrap tail of 1/40 sits ~7.5% and PASSES — the flag must fire, and the
    # row must say Wilson stands (D4)
    m1_root, m2_root, models = _synthetic_evidence(tmp_path)
    rows = appendix(m1_root, m2_root, models=models, blank_models=("emitter",), b=5000)
    row = {(r["model"], r["label"]): r for r in rows}[("waller", "lossy@0.1")]
    assert row["gate"] == "ceiling"
    assert row["wilson_pass"] is False
    assert row["boot_pass"] is True
    assert row["disagree"] is True
    # ungated component cells carry no flag at all
    sf = {(r["model"], r["label"]): r for r in rows}[("waller", "source_first@0.1")]
    assert sf["gate"] is None and sf["disagree"] is None


def test_equivalence_rows_gate_on_containment_not_excludes_zero(tmp_path):
    m1_root, m2_root, models = _synthetic_evidence(tmp_path)
    rows = appendix(m1_root, m2_root, models=models, blank_models=("emitter",), b=200)
    eq = {(r["model"], r["label"]): r for r in rows}[
        ("waller", "equivalence padded−lossy @0.3")]
    assert eq["gate"] == "contained"
    d, lo, hi = newcombe_diff(0, 40, 0, 40)          # padded 0/40 vs lossy 0/40
    assert eq["wilson_pass"] is (-m2.DELTA < lo and hi < m2.DELTA)
    assert eq["wilson_pass"] is True                 # ±8.8% sits inside ±10%


def test_format_appendix_prints_both_methods_and_the_d4_rule(tmp_path):
    m1_root, m2_root, models = _synthetic_evidence(tmp_path)
    rows = appendix(m1_root, m2_root, models=models, blank_models=("emitter",), b=200)
    text = format_appendix(rows)
    assert "Wilson" in text and "bootstrap" in text
    assert "Wilson decides" in text                  # D4, restated where the table lives
    assert "DISAGREE" in text                        # the engineered 1/40 row is flagged
    assert "lossy@0.1" in text and "emission gap lossy−blank" in text


# ── the real archived record, wired through the same path ────────────────────────────

def test_appendix_over_the_real_archived_evidence_pins_the_judged_numbers():
    rows = appendix("evidence/m1", "evidence/m2", b=50)   # tiny B: wiring, not intervals
    assert len(rows) == 3 * 2 * 6 + 3                     # the brief's ~40: exactly 39
    by = {(r["model"], r["label"]): r for r in rows}
    assert (by[("llama", "lossy@0.1")]["k"], by[("llama", "lossy@0.1")]["n"]) == (0, 40)
    assert (by[("deepseek", "lossy@0.1")]["k"], by[("deepseek", "lossy@0.1")]["n"]) == (1, 90)
    assert (by[("qwen72b", "lossy_padded@0.3")]["k"],
            by[("qwen72b", "lossy_padded@0.3")]["n"]) == (1, 90)
    gap = by[("deepseek", "emission gap lossy−blank")]
    assert (gap["k_mech"], gap["n_mech"], gap["k_base"], gap["n_base"]) == (52, 90, 0, 40)
    # every real gated row agrees across methods — the appendix's expected headline
    flagged = [r for r in rows if r["disagree"]]
    assert flagged == []


def test_constants_are_imported_never_redefined():
    assert bootstrap.CEILING is m1.CEILING
    assert bootstrap.DELTA is m2.DELTA
    assert bootstrap.ROSTER is m1.ROSTER
    assert bootstrap.BLANK_MODELS is m2.BLANK_MODELS
    assert bootstrap.GATED_G == (0.1, 0.3)
