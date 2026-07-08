"""test_m4.py — the M4 driver's free-testable parts. No network, no cost.

What's pinned here, before any paid call (m0's D8/D9 pattern — verdicts pre-committed
in code so they can't bend after data arrives):

  - the PAPER anchor (rider a): the arXiv v2 Table 6 llama·logic wall cells, from the
    two-pass verbatim extraction of 2026-07-08 (evidence/m4/paper-extraction-logic.md).
    The paper's committed values are the comparison target, NOT the README artifact's —
    the two disagree on every llama·logic cell (M3 precedent, larger here), and the
    variance is footnoted in the evidence file. No gate touches these numbers.
  - D24's pilot tier IS D8's (imported, never redefined): ≥70% green, 50–70% amber,
    <50% trigger — the 14/10-at-20 lines.
  - the D25 gates with their boundary arithmetic asserted, not assumed: the claim-1
    GAP gate (Newcombe on source_first − lossy, positive at both wall g — no lossy
    ceiling on a soft wall), the claim-2 SEPARATION gate (sf − padded), the anchored
    shape read (v1's pre-committed smallness scale CEILING=0.10, mirrored at both
    ends: a floor "consistent with ~0" or a fix "consistent with ~1" is the
    arithmetic regime, not the paper's soft wall), and the verdict mapping
    REPRODUCED / PARTIAL / NULL / DISCREPANT — DISCREPANT reachable only through a
    scope-B cross-check result.
  - the equivalence (padded ≈ lossy) is REPORTED, never gated: δ=0.10 equivalence is
    unpowerable at hobby N on a mid-range rate (the brief's [−0.15, +0.15] at N=60).
  - the four-way taxonomy summary with the chance floor (~1/k) stated per cell.
  - D26: N=60 flat, the N=20 checkpoint, and NO escalation ladder.
  - the m4 problem schedule (fresh per trial, D5, alternating the author's two logic
    grammars) and the pilot/bank/grid drivers end-to-end on deterministic fakes.

The LogicWallFake is this file's hand-crank (test_m1's WallFake, re-tuned for text):
session 1 always commits the drift token; session 2 recovers the correct token exactly
when the clue set is in context — no randomness, so cell counts are exact.
"""
from __future__ import annotations

import json

import pytest

import m0
import m1
import m4
from grader import ABST, INHERIT, NOVEL, RECOV
from m4 import (DISCREPANT, GRID_G, GRID_POLICIES, N_BANK, N_CHECKPOINT, NULL, PAPER,
                PARTIAL, REPRODUCED, anchor_shape_matches, bank_problem, checkpoint,
                claim_model_verdict, equivalence_report, gap_gate, judge, load_bank,
                m4_claim_verdict, make_figure, pilot_problem, pilot_tier, run_bank,
                run_grid, run_pilot, shape_reads, taxonomy_summary)
from problems import Problem

FAKES = {"fakea": "fake/model-a", "fakeb": "fake/model-b"}


class LogicWallFake:
    """Deterministic soft-wall-free behaviour: session 1 always commits the drift
    token (take = n/n); session 2 recovers iff the clue set is present in context —
    the anti-rig property with the noise removed."""

    def __init__(self, problem: Problem):
        self.problem = problem

    def chat(self, messages) -> str:
        last = (messages[-1].get("content") or "").lower()
        if "recheck" in last or "wrong" in last:
            if any(self.problem.facts[:18].lower() in (m.get("content") or "").lower()
                   for m in messages):
                return f"Rechecking... ANSWER: {self.problem.correct}"
            return (f"I am not sure I have enough to recompute. "
                    f"ANSWER: {self.problem.drift}")
        return f"Using what was given, ANSWER: {self.problem.drift}"


class NoTakeLogicFake:
    """Never takes: re-derives and answers the correct token from the start."""

    def __init__(self, problem: Problem):
        self.problem = problem

    def chat(self, messages) -> str:
        return f"ANSWER: {self.problem.correct}"


def wall_factory():
    return lambda slug, problem: LogicWallFake(problem)


# ── the PAPER anchor (rider a) and the settled constants ─────────────────────────────

def test_paper_anchor_is_the_arxiv_v2_table():
    # llama·logic wall cells as the paper v2 prints them (Table 6), two-pass verbatim;
    # the README artifact disagrees on every one of these cells (footnoted in
    # evidence/m4/paper-extraction-logic.md) — the PAPER values are the target
    assert PAPER["llama"]["lossy"] == {0.3: 0.16, 0.1: 0.05}
    assert PAPER["llama"]["lossy_padded"] == {0.3: 0.18, 0.1: 0.09}
    assert PAPER["llama"]["source_first"] == {0.3: 0.76, 0.1: 0.79}
    assert "Table 6" in m4.PAPER_SOURCE and "arXiv" in m4.PAPER_SOURCE


def test_d26_constants():
    assert N_BANK == 60 and N_CHECKPOINT == 20
    assert GRID_G == (0.1, 0.3)
    assert GRID_POLICIES == ("lossy", "lossy_padded", "source_first")
    assert not hasattr(m4, "N_MAX"), "D26: no escalation ladder on the soft wall"


def test_d10_and_d13_are_imported_never_redefined():
    assert m4.TEMPERATURE == m0.TEMPERATURE and m4.MAX_TOKENS == m0.MAX_TOKENS
    assert m4.ROSTER is m1.ROSTER


def test_d24_tier_is_d8s():
    assert pilot_tier is m0.d8_verdict           # imported, never redefined
    assert pilot_tier(14, 20) == "green"
    assert pilot_tier(13, 20) == "amber"
    assert pilot_tier(10, 20) == "amber"
    assert pilot_tier(9, 20) == "trigger"


# ── the D25 gates: boundary arithmetic asserted, not assumed ─────────────────────────

def test_gap_gate_boundary_arithmetic():
    # the anchor-shaped case at N=60 (lossy 15/60 vs sf 40/60): decisively positive
    g = gap_gate(15, 60, 40, 60)
    assert round(g["d"], 4) == 0.4167
    assert round(g["lo"], 4) == 0.2410 and g["positive"]
    # a near-tie cannot clear (20/60 vs 22/60 straddles zero)
    assert not gap_gate(20, 60, 22, 60)["positive"]
    # direction matters: a NEGATIVE gap is not a pass
    assert not gap_gate(40, 60, 15, 60)["positive"]


def test_shape_reads_mirrored_ceiling():
    # soft floor: 2/60 (Wilson hi .1136) is NOT consistent-with-~0 → soft;
    # 0/60 (hi .0602) would have cleared v1's ceiling → collapsed (harder than paper)
    r = shape_reads(2, 60, 40, 60)
    assert r["floor_soft"] and r["sf_below_one"] and r["gap_positive"]
    assert not shape_reads(0, 60, 40, 60)["floor_soft"]
    # the mirrored top: sf 59/60 (Wilson lo .9114 ≥ .90) reads as "reaches ~1";
    # 58/60 (lo .8864) does not
    assert not shape_reads(2, 60, 59, 60)["sf_below_one"]
    assert shape_reads(2, 60, 58, 60)["sf_below_one"]
    # and the gap read is the claim-1 gate itself
    assert not shape_reads(20, 60, 22, 60)["gap_positive"]


def test_anchor_shape_needs_all_reads_at_both_g():
    ok = {"0.3": shape_reads(10, 60, 45, 60), "0.1": shape_reads(3, 60, 47, 60)}
    assert anchor_shape_matches(ok)
    bad = dict(ok, **{"0.1": shape_reads(0, 60, 47, 60)})   # collapsed floor at one g
    assert not anchor_shape_matches(bad)


def test_claim_model_verdict_composition():
    assert claim_model_verdict({"0.1": True, "0.3": True}) == "cleared"
    assert claim_model_verdict({"0.1": True, "0.3": False}) == "partial"
    assert claim_model_verdict({"0.1": False, "0.3": False}) == "not_cleared"


def test_m4_claim_verdict_mapping():
    two = {"llama": "cleared", "deepseek": "cleared", "qwen72b": "not_cleared"}
    # REPRODUCED: the ≥2-model bar AND the anchored shape
    assert m4_claim_verdict(two, anchor_shape=True) == REPRODUCED
    # the bar met but the shape diverges → structure, not a pass
    assert m4_claim_verdict(two, anchor_shape=False) == PARTIAL
    # one cleared model is under the bar
    one = {"llama": "cleared", "deepseek": "partial", "qwen72b": "not_cleared"}
    assert m4_claim_verdict(one, anchor_shape=True) == PARTIAL
    # NULL is pre-registered: no gap anywhere (sf ≈ lossy)
    none = {k: "not_cleared" for k in two}
    assert m4_claim_verdict(none, anchor_shape=False) == NULL
    # claim 2 has no shape clause (anchor_shape=None)
    assert m4_claim_verdict(two, anchor_shape=None) == REPRODUCED
    # DISCREPANT only through a scope-B cross-check result
    assert m4_claim_verdict(two, anchor_shape=True, crosscheck="discrepant") == DISCREPANT
    assert m4_claim_verdict(two, anchor_shape=True, crosscheck="agree") == REPRODUCED


def test_equivalence_is_reported_never_gated():
    r = equivalence_report(15, 60, 15, 60)
    assert r["overlaps_zero"] and r["d"] == 0.0
    assert "unpowerable" in r["caveat"]
    assert "verdict" not in r          # descriptive: no pass/fail key exists
    assert not equivalence_report(15, 60, 40, 60)["overlaps_zero"]


def test_taxonomy_summary_counts_and_chance_floor():
    rows = [{"bucket": RECOV, "k_options": 3}, {"bucket": INHERIT, "k_options": 3},
            {"bucket": INHERIT, "k_options": 4}, {"bucket": ABST, "k_options": 4}]
    s = taxonomy_summary(rows)
    assert s["n"] == 4
    assert s["counts"] == {RECOV: 1, INHERIT: 2, NOVEL: 0, ABST: 1}
    assert round(s["chance_floor"], 4) == 0.2917    # mean of 1/3,1/3,1/4,1/4


# ── the m4 problem schedules (fresh per trial, D5, both grammars) ────────────────────

def test_bank_problem_is_deterministic_fresh_and_alternating():
    p0, p1 = bank_problem(0, 0), bank_problem(0, 1)
    assert p0 == bank_problem(0, 0)                 # same (seed, trial) → same problem
    assert p0.pid == "m4g0-00" and p1.pid == "m4g0-01"
    assert p0.kind == "text" and p1.kind == "text"
    assert p0.ask.startswith("the runner")          # even trial: ordering grammar
    assert p1.ask.startswith("the person with")     # odd trial: assignment grammar
    assert bank_problem(0, 2) != p0                 # fresh per trial
    assert bank_problem(1, 0) != p0                 # fresh per seed


def test_pilot_problems_are_their_own_namespace():
    q = pilot_problem(0, 0)
    assert q.pid == "m4p0-00" and q != bank_problem(0, 0)


def test_schedule_problems_validate():
    for t in range(8):
        assert bank_problem(0, t).correct != bank_problem(0, t).drift
        assert pilot_problem(0, t).correct in pilot_problem(0, t).options


# ── the D24 pilot on fakes ────────────────────────────────────────────────────────────

def test_run_pilot_takes_and_reads_disposition(tmp_path):
    out = run_pilot(wall_factory(), n=6, seed=0, runs_root=tmp_path, models=FAKES)
    for key in FAKES:
        r = out[key]
        assert r["takes"] == 6 and r["n"] == 6 and r["tier"] == "green"
        # the disposition read on the wall cell: the fake commits the drift token
        # whenever the clues are absent → all INHERIT, never ABST
        assert r["taxonomy"]["counts"][INHERIT] == 6
        assert r["taxonomy"]["counts"][RECOV] == 0
        rows = [json.loads(line) for line in
                (tmp_path / f"m4-pilot-{key}" / "results.jsonl").read_text().splitlines()]
        assert len(rows) == 6 and all(row["took"] for row in rows)
        assert all(row["wall_bucket"] == INHERIT for row in rows)


def test_run_pilot_trigger_on_a_no_take_model(tmp_path):
    llm_for = lambda slug, problem: NoTakeLogicFake(problem)   # noqa: E731
    out = run_pilot(llm_for, n=6, seed=0, runs_root=tmp_path,
                    models={"fakea": FAKES["fakea"]})
    r = out["fakea"]
    assert r["takes"] == 0 and r["tier"] == "trigger"
    assert r["taxonomy"]["n"] == 0        # no taken trials → no wall reads


# ── the bank and the grid on fakes ────────────────────────────────────────────────────

def test_run_bank_reaches_target_and_resumes(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    res = run_bank(wall_factory(), target=3, seed=0, runs_root=tmp_path, models=models)
    assert res["fakea"]["takes"] == 3 and not res["fakea"]["short"]
    res = run_bank(wall_factory(), target=5, seed=0, runs_root=tmp_path, models=models)
    assert res["fakea"]["takes"] == 5
    rows = [json.loads(line) for line in
            (tmp_path / "m4-bank-fakea" / "results.jsonl").read_text().splitlines()]
    assert len(rows) == 5                                  # extended, never re-run
    assert [r["trial"] for r in rows] == list(range(5))
    assert rows[0]["pid"].startswith("m4g0-")


def test_load_bank_refuses_a_foreign_schedule(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(wall_factory(), target=2, seed=0, runs_root=tmp_path, models=models)
    assert len(load_bank(tmp_path, "fakea", seed=0)) == 2
    with pytest.raises(ValueError):
        load_bank(tmp_path, "fakea", seed=7)


def test_run_grid_runs_all_cells_flat_and_extends(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(wall_factory(), target=3, seed=0, runs_root=tmp_path, models=models)
    run_grid(wall_factory(), n=2, seed=0, runs_root=tmp_path, models=models)
    run_grid(wall_factory(), n=3, seed=0, runs_root=tmp_path, models=models)
    rows = [json.loads(line) for line in
            (tmp_path / "m4-grid-fakea" / "results.jsonl").read_text().splitlines()]
    assert len(rows) == 3 * len(GRID_POLICIES) * len(GRID_G)   # no duplicates, no cap
    one = rows[0]
    for field in ("bank_trial", "pid", "policy", "g", "note", "reply", "bucket",
                  "reclaimed", "k_options", "model", "temperature", "cost"):
        assert field in one, f"grid row missing {field}"
    # the fake's wall: sf recovers, lossy/padded inherit
    for r in rows:
        if r["policy"] == "source_first":
            assert r["bucket"] == RECOV and r["reclaimed"]
        else:
            assert r["bucket"] == INHERIT and not r["reclaimed"]


# ── checkpoint and judge: pure readers of the logged rows ─────────────────────────────

def _write_grid_rows(root, key: str, cells: dict[str, tuple[int, int]]) -> None:
    """Synthetic grid JSONL: cells maps 'policy@g' → (k recovered, n), buckets
    INHERIT for the misses, k_options fixed at 3."""
    d = root / f"m4-grid-{key}"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "results.jsonl", "w", encoding="utf-8") as f:
        for ck, (k, n) in cells.items():
            policy, g = ck.split("@")
            for i in range(n):
                row = {"bank_trial": i, "pid": f"syn-{i}", "policy": policy,
                       "g": float(g), "bucket": RECOV if i < k else INHERIT,
                       "reclaimed": i < k, "k_options": 3, "hedged": False}
                f.write(json.dumps(row) + "\n")


SOFT_CELLS = {"lossy@0.1": (3, 60), "lossy@0.3": (10, 60),
              "lossy_padded@0.1": (5, 60), "lossy_padded@0.3": (11, 60),
              "source_first@0.1": (47, 60), "source_first@0.3": (45, 60)}


def test_judge_reproduced_on_soft_wall_rows(tmp_path):
    for key in FAKES:
        _write_grid_rows(tmp_path, key, SOFT_CELLS)
    out = judge(tmp_path, models=FAKES, anchor="fakea")
    for key in FAKES:
        m = out["models"][key]
        assert m["claim1_verdict"] == "cleared" and m["claim2_verdict"] == "cleared"
        assert m["cells"]["lossy@0.1"]["k"] == 3
        assert m["cells"]["lossy@0.1"]["chance_floor"] == pytest.approx(1 / 3)
        assert m["equivalence"]["0.1"]["overlaps_zero"]
    assert out["anchor_shape"]["matches"] is True
    assert out["claim1"] == REPRODUCED and out["claim2"] == REPRODUCED


def test_judge_null_when_the_fix_does_not_generalize(tmp_path):
    flat = {ck: (12, 60) for ck in SOFT_CELLS}      # sf ≈ lossy everywhere
    for key in FAKES:
        _write_grid_rows(tmp_path, key, flat)
    out = judge(tmp_path, models=FAKES, anchor="fakea")
    assert out["claim1"] == NULL and out["claim2"] == NULL


def test_judge_partial_when_anchor_shape_diverges(tmp_path):
    hard = dict(SOFT_CELLS, **{"lossy@0.1": (0, 60), "lossy@0.3": (0, 60)})   # arithmetic-hard floor
    for key in FAKES:
        _write_grid_rows(tmp_path, key, hard)
    out = judge(tmp_path, models=FAKES, anchor="fakea")
    assert out["anchor_shape"]["matches"] is False
    assert out["claim1"] == PARTIAL                 # gap clears, shape diverges
    assert out["claim2"] == REPRODUCED              # claim 2 carries no shape clause


def test_checkpoint_samples_for_the_hand_read(tmp_path):
    _write_grid_rows(tmp_path, "fakea", SOFT_CELLS)
    out = checkpoint(tmp_path, models={"fakea": FAKES["fakea"]}, sample_k=3)
    cells = out["fakea"]["cells"]
    assert set(cells) == set(SOFT_CELLS)
    for c in cells.values():
        assert len(c["sample"]) == 3 and c["n"] == 60
    # the light futility note (D26): the gap trend is reported, nothing gates or stops
    assert "gap_trend" in out["fakea"]


def test_figure_writes_png(tmp_path):
    for key in FAKES:
        _write_grid_rows(tmp_path, key, SOFT_CELLS)
    out = judge(tmp_path, models=FAKES, anchor="fakea")
    path = tmp_path / "m4-logic-wall.png"
    make_figure(out, path)
    assert path.exists() and path.stat().st_size > 0
