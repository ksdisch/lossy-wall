"""test_m5.py — the source-size boundary arm (D28-B, the paper's design), $0. Pins D29's
cliff gate + verdict mapping as pure functions BEFORE any data exists (the pre-commitment
that makes the gate a gate), plus the K-item generator, the budget-fit note builder, and the
graded source gate.

The D29 boundary arithmetic is pinned with hand-picked (k, n) whose Wilson/Newcombe outcomes
are independent of the gate code, so the gate cannot be quietly bent to fit a result later.
Synthetic-rows judge tests wire the whole mapping (REPRODUCED / NULL) end to end.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from m5 import (BUDGETS, CLIFF_CEIL, NULL, PARTIAL, REPRODUCED, ceiling_intact,
                cliff_verdict, crossover_n, judge, mechanism_gate, monotone_within_noise,
                real_drop, tracks_budget)
from notes import build_sized_note, item_clauses, memory_note_sized, retained_fraction
from problems import generate_sized, validate
from runner import SourceGateError, run_session2_budget
from fake import SourceSizeFake
from grader import ABSTAIN, EMIT_ATTRACTOR, RECLAIMED, grade, took
from runner import build_trajectory, last_answer


# ── the K-item generator (variable N) ─────────────────────────────────────────────────

def test_generate_sized_varies_n():
    for n in (2, 6, 12, 24):
        p = generate_sized(random.Random(n), f"m5t-{n}", k_items=n)
        assert len(item_clauses(p.facts)) == n
        assert abs(p.correct - p.drift) >= 7
        validate(p)


def test_generate_sized_is_pure():
    assert generate_sized(random.Random(7), "x", 8) == generate_sized(random.Random(7), "x", 8)


# ── the budget-fit note + the graded source gate ────────────────────────────────────

def _problem(n=8):
    return generate_sized(random.Random(42), "m5t", k_items=n)


def test_build_sized_note_fits_whole_items_to_budget():
    p = _problem(8)
    # a huge budget keeps every item (k == N)
    note, k = build_sized_note(p, 100000, "source_first")
    assert k == 8 and retained_fraction(note, p) == pytest.approx(1.0)
    # the budget that exactly holds the 3-item note keeps 3
    note3 = memory_note_sized(p, "source_first", 3)
    note, k = build_sized_note(p, len(note3), "source_first")
    assert k == 3 and retained_fraction(note, p) == pytest.approx(3 / 8)
    # a tiny budget starves it to zero items
    _note, k0 = build_sized_note(p, 80, "source_first")
    assert k0 == 0


def test_lossy_padded_is_budget_matched_floor():
    p = _problem(8)
    for budget in (300, 600):
        sf, _ = build_sized_note(p, budget, "source_first")
        lp, k = build_sized_note(p, budget, "lossy_padded")
        assert k == 0 and retained_fraction(lp, p) == 0.0      # carries no source
        assert len(lp) >= len(sf)                              # matched to source_first length
        assert f"{p.drift:g}" in lp                            # carries the stale conclusion


def test_build_sized_note_rejects_bad_policy():
    with pytest.raises(ValueError):
        build_sized_note(_problem(), 300, "lossy")             # bare lossy not an M5 arm


def test_run_session2_budget_returns_note_and_k_and_gates():
    p = _problem(8)
    reply, note, k = run_session2_budget(SourceSizeFake(p), p, 100000, "source_first")
    assert "ANSWER:" in reply and k == 8
    assert retained_fraction(note, p) == pytest.approx(1.0)


def test_size_gate_raises_on_tampered_note(monkeypatch):
    # if the gate ever saw a note whose source content disagreed with its k, it must refuse
    from runner import verify_size_gate
    p = _problem(8)
    note4 = memory_note_sized(p, "source_first", 4)            # carries 4 items
    verify_size_gate(note4, p, "source_first", 4)              # matches → no raise
    with pytest.raises(SourceGateError):
        verify_size_gate(note4, p, "source_first", 2)          # claims 2, carries 4


# ── D29 gate pure functions: pinned boundary arithmetic (pre-commitment) ─────────────

def test_ceiling_intact_boundary():
    assert ceiling_intact(20, 20) is True             # wilson lo 0.839 ≥ 0.80
    assert ceiling_intact(15, 20) is False            # wilson lo ~0.53 < 0.80
    assert ceiling_intact(38, 40) is True


def test_real_drop_excludes_zero_only_when_real():
    assert real_drop(20, 20, 0, 20)["positive"] is True       # 1.0 → 0.0 as N grows
    assert real_drop(20, 20, 18, 20)["positive"] is False     # 1.0 vs 0.9 — no separation


def test_monotone_within_noise():
    assert monotone_within_noise([(20, 20), (14, 20), (6, 20), (0, 20)]) is True
    assert monotone_within_noise([(6, 20), (20, 20)]) is False    # RR rises as N grows
    assert monotone_within_noise([(20, 20), (19, 20), (18, 20)]) is True   # within noise


def test_crossover_n_is_largest_n_above_half():
    sf = [{"N": 2, "rate": 1.0}, {"N": 4, "rate": 0.9}, {"N": 8, "rate": 0.6},
          {"N": 12, "rate": 0.2}, {"N": 24, "rate": 0.0}]
    assert crossover_n(sf) == 8
    assert crossover_n([{"N": 2, "rate": 0.1}]) is None


def test_mechanism_gate_full_vs_partial():
    assert mechanism_gate(60, 60, 0, 60)["positive"] is True   # full 1.0 vs partial 0.0
    assert mechanism_gate(30, 60, 28, 60)["positive"] is False


def test_tracks_budget():
    assert tracks_budget({300: 6, 600: 16}) is True
    assert tracks_budget({300: 16, 600: 6}) is False
    assert tracks_budget({300: 6, 600: None}) is None
    assert tracks_budget({300: 6}) is None                     # needs two budgets


def test_cliff_verdict_mapping():
    both_cliff = {300: {"ceiling": True, "drop_positive": True, "monotone": True, "robust": False},
                  600: {"ceiling": True, "drop_positive": True, "monotone": True, "robust": False}}
    assert cliff_verdict(both_cliff, tracks=True, mech_positive=True) == REPRODUCED
    assert cliff_verdict(both_cliff, tracks=False, mech_positive=True) == PARTIAL   # no budget-track
    assert cliff_verdict(both_cliff, tracks=True, mech_positive=False) == PARTIAL   # no mechanism
    assert cliff_verdict(both_cliff, tracks=True, mech_positive=True,
                         confound_clean=False) == PARTIAL                           # confound
    no_cliff = {300: {"ceiling": True, "drop_positive": False, "monotone": True, "robust": True},
                600: {"ceiling": True, "drop_positive": False, "monotone": True, "robust": True}}
    assert cliff_verdict(no_cliff, tracks=None, mech_positive=None) == NULL
    one_only = {300: {"ceiling": True, "drop_positive": True, "monotone": True, "robust": False},
                600: {"ceiling": True, "drop_positive": False, "monotone": True, "robust": False}}
    assert cliff_verdict(one_only, tracks=None, mech_positive=True) == PARTIAL


# ── synthetic-rows judge: the mapping wired end to end ────────────────────────────────

def _write_grid(tmp_path: Path, key: str, spec: dict):
    """spec: (N, budget, policy) -> (k_reclaim, n, full_source)."""
    d = tmp_path / f"m5-grid-{key}"
    d.mkdir(parents=True)
    rows = []
    for (N, budget, policy), (k, n, full) in spec.items():
        for i in range(n):
            reclaimed = i < k
            rows.append({"bank_trial": i, "pid": f"m5g0n{N}-{i:02d}", "N": N,
                         "budget": budget, "policy": policy, "k_kept": N if full else 1,
                         "full_source": full, "reclaimed": reclaimed,
                         "outcome": "reclaimed" if reclaimed else "emit_attractor"})
    (d / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_judge_reproduced_on_the_paper_pattern(tmp_path):
    # crossover tracks the budget (B=300 → 2, B=600 → 8), full≫partial, monotone cliffs
    sf = {(2, 300): (20, 20, True), (8, 300): (0, 20, False), (24, 300): (0, 20, False),
          (2, 600): (20, 20, True), (8, 600): (20, 20, True), (24, 600): (0, 20, False)}
    spec = {}
    for (N, b), v in sf.items():
        spec[(N, b, "source_first")] = v
        spec[(N, b, "lossy_padded")] = (0, 20, False)
    _write_grid(tmp_path, "deepseek", spec)
    m = judge(str(tmp_path), {"deepseek": "slug"})["models"]["deepseek"]
    assert m["crossovers"] == {300: 2, 600: 8}
    assert m["tracks_budget"] is True
    assert m["mechanism"]["positive"] is True
    assert all(pb["ceiling"] and pb["drop_positive"] and pb["monotone"]
               for pb in m["per_budget"].values())
    assert m["verdict"] == REPRODUCED


def test_judge_null_when_fix_survives_growth(tmp_path):
    # source_first stays high at every N and budget (no cliff) → NULL
    spec = {}
    for b in (300, 600):
        for N in (2, 8, 24):
            spec[(N, b, "source_first")] = (19, 20, True)
            spec[(N, b, "lossy_padded")] = (0, 20, False)
    _write_grid(tmp_path, "deepseek", spec)
    m = judge(str(tmp_path), {"deepseek": "slug"})["models"]["deepseek"]
    assert all(not pb["drop_positive"] and pb["robust"] for pb in m["per_budget"].values())
    assert m["verdict"] == NULL


# ── a fake-driven end-to-end: the cliff + the silent mis-sum ─────────────────────────

def test_fake_reclaims_full_source_and_silently_missums_when_starved():
    """SourceSizeFake (= the author's SizeFake) reclaims only with the COMPLETE source,
    and past the cliff EMITS THE DRIFT (silent mis-sum), not an abstention — the paper's
    worse-than-empty finding, mechanized."""
    p = _problem(8)
    reply_full, _, k = run_session2_budget(SourceSizeFake(p), p, 100000, "source_first")
    assert k == 8 and grade(reply_full, p).outcome == RECLAIMED
    reply_starved, _, k2 = run_session2_budget(SourceSizeFake(p), p, 150, "source_first")
    assert k2 < 8
    assert grade(reply_starved, p).outcome == EMIT_ATTRACTOR      # the silent mis-sum
    reply_pad, _, _ = run_session2_budget(SourceSizeFake(p), p, 600, "lossy_padded")
    assert grade(reply_pad, p).outcome == EMIT_ATTRACTOR          # no source → mis-sum too


def test_fake_drift_takes_on_k_item_receipts():
    for i in range(6):
        p = generate_sized(random.Random(100 + i), f"m5t-{i}", k_items=6)
        traj = build_trajectory(SourceSizeFake(p, seed=i), p)
        assert took(last_answer(traj), p), f"{p.pid}: no drift take"


def test_budgets_are_the_two_paper_budgets():
    assert BUDGETS == (300, 600)
