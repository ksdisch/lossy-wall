"""test_m2.py — the M2 controls-grid driver's free-testable parts. No network, no cost.

What's pinned here, before any paid call (the D14 pattern — verdicts pre-committed in
code so they can't bend after data arrives):
  - D16's containment ladder EXACTLY as recorded in DECISIONS.md: nothing judged below
    N=40 and NO numeric futility shortcut anywhere; the Newcombe 95% interval on
    (lossy_padded − lossy) must sit entirely inside ±δ = ±0.10 (D7) at N=40; not
    contained at 40 → extend ONCE to ≈90 and judge final — with the boundary
    arithmetic asserted, not assumed, including the comparator-dependence fact that
    bans any fixed cutoff (4/90 FAILS against a 0/40 comparator at +10.9% but CLEARS
    against deepseek's archived 1/90 at +9.8%);
  - claim 2's composition (mirrors D14): BOTH components — containment AND the
    (source_first − lossy_padded) separation excluding zero — at BOTH wall g; the v1
    rollup is D14's own ≥2-of-3 rule, imported from m1, never redefined;
  - claim 3's counting rule (committed blind 2026-07-07, D17): wrong emission iff the
    logged outcome is emit_attractor or emit_other_wrong, tallied from rows only at
    judge time; gate = Newcombe on wrong-emission (lossy − blank) excludes zero;
  - the cell plan: 2 padded + 4 knob cells per model, blank on deepseek only; knob and
    blank fixed at N=40 (D18/D17) — only padded cells ladder toward 90;
  - the grid runner on fakes: bank-order trials over M1's banks, resume/extend without
    duplicates, the g=1.0 transcript cell carrying the FULL session-1 trajectory from
    the bank's trial files (note=None on its rows), per-trial source gates held in the
    right direction on every note cell;
  - the checkpoint (counts + the ≥3-trial hand-read sample, NO futility flags — none
    of M2's cells carries a reclaim ceiling) and the judge (a pure function of the
    m1 + m2 logged rows), including the sf@0.6 ≡ sf@1.0 replicate check and the merged
    cell table the knob figure draws from.

M2WallFake is this file's hand-crank: WallFake (session 2 reclaims iff the facts
marker is in context) plus the transcript anchor — it also reclaims when the ORIGINAL
QUESTION is present, which is how the g=1.0 transcript cell carries the source.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

import m0
import m1
import m2
from grader import OUTCOMES
from m1 import bank_problem, run_bank
from m2 import (claim2_model_verdict, claim3_verdict, emission_split,
                load_trajectory, make_emission_figure, make_knob_figure,
                padded_cell_verdict, run_grid)
from notes import memory_note, source_present
from runner import expected_source_presence
from stats import newcombe_diff
from test_m1 import FAKES, WallFake


class M2WallFake(WallFake):
    """WallFake plus the transcript anchor: session 2 reclaims when the recomputable
    source is present either as the facts string (a note that kept it) or as the
    original question (the g=1.0 transcript cell) — the left-anchor behaviour the
    real transcript cells are expected to show."""

    def chat(self, messages) -> str:
        last = (messages[-1].get("content") or "").lower()
        if ("recheck" in last or "wrong" in last) and any(
                self.problem.question in (m.get("content") or "") for m in messages):
            return f"Rechecking... ANSWER: {self.problem.correct:g}"
        return super().chat(messages)


def m2_factory():
    return lambda slug, problem: M2WallFake(problem)


# ── constants: imported, never redefined (D10 sampling; m1's roster and N schedule) ──

def test_constants_are_imported_never_redefined():
    assert m2.TEMPERATURE is m0.TEMPERATURE
    assert m2.MAX_TOKENS is m0.MAX_TOKENS
    assert m2.ROSTER is m1.ROSTER
    assert m2.load_bank is m1.load_bank
    assert (m2.N_CHECKPOINT, m2.N_JUDGE, m2.N_MAX) == (20, 40, 90)
    # the run caps default to m1's constants: knob/blank fixed at 40, padded to 90
    sig = inspect.signature(run_grid)
    assert sig.parameters["knob_cap"].default == m1.N_JUDGE
    assert sig.parameters["pad_cap"].default == m1.N_MAX


def test_d7_delta_and_the_m2_cells():
    assert m2.DELTA == 0.10                    # D7, committed at the M0 sign-off
    assert m2.PADDED_G == (0.1, 0.3)           # claim 2 at both wall g (D16)
    assert m2.KNOB_G == (0.6, 1.0)             # the descriptive fills (D18)
    assert m2.BLANK_MODELS == ("deepseek",)    # the roster's only emitter (D17)
    assert m2.BLANK_G == 0.1                   # blank is g-independent; logged at the wall locus


def test_cell_plan_two_padded_four_knob_blank_on_deepseek_only():
    plan = m2.cell_plan("deepseek")
    assert plan == [("lossy_padded", 0.1), ("lossy_padded", 0.3),
                    ("lossy", 0.6), ("lossy", 1.0),
                    ("source_first", 0.6), ("source_first", 1.0),
                    ("blank", 0.1)]
    assert m2.cell_plan("llama") == plan[:-1]
    assert m2.cell_plan("qwen72b") == plan[:-1]


def test_figure_paths_are_new_files_m1_wall_untouched():
    assert m2.KNOB_FIGURE_PATH == Path("docs/figs/m2-knob.png")
    assert m2.EMISSION_FIGURE_PATH == Path("docs/figs/m2-emission.png")
    assert m1.FIGURE_PATH == Path("docs/figs/m1-wall.png")   # M1's committed record


# ── the D16 containment ladder — boundary arithmetic asserted, not assumed ───────────
# Orientation everywhere: d = (lossy_padded − lossy), i.e. newcombe_diff(base=lossy
# comparator, mech=padded). Containment: the interval sits entirely inside ±DELTA.

def test_d16_boundary_arithmetic_vs_a_clean_0_of_40_comparator():
    d, lo, hi = newcombe_diff(0, 40, 0, 40)
    assert lo == pytest.approx(-0.088, abs=5e-4)             # ±8.8%: contained
    assert hi == pytest.approx(+0.088, abs=5e-4)
    assert newcombe_diff(0, 40, 1, 40)[2] == pytest.approx(0.129, abs=5e-4)  # escalate
    d, lo, hi = newcombe_diff(0, 40, 1, 90)
    assert lo == pytest.approx(-0.077, abs=5e-4)             # clears after escalation
    assert hi == pytest.approx(+0.060, abs=5e-4)
    assert newcombe_diff(0, 40, 4, 90)[2] == pytest.approx(0.109, abs=5e-4)  # fails


def test_d16_boundary_arithmetic_vs_deepseeks_1_of_90_comparator():
    d, lo, hi = newcombe_diff(1, 90, 0, 40)
    assert lo == pytest.approx(-0.060, abs=5e-4)
    assert hi == pytest.approx(+0.077, abs=5e-4)
    assert newcombe_diff(1, 90, 1, 40)[2] == pytest.approx(0.118, abs=5e-4)  # escalate
    d, lo, hi = newcombe_diff(1, 90, 1, 90)
    assert lo == pytest.approx(-0.050, abs=5e-4)             # ±5.0%: clears
    assert hi == pytest.approx(+0.050, abs=5e-4)
    assert newcombe_diff(1, 90, 4, 90)[2] == pytest.approx(0.098, abs=5e-4)  # clears


def test_d16_nothing_judged_below_40_and_no_futility_shortcut():
    assert padded_cell_verdict(0, 20, 0, 40) == "continue"
    assert padded_cell_verdict(0, 39, 0, 40) == "continue"
    # 4 strays at the checkpoint would be FUTILE under D14 — D16 bans that shortcut
    # for padded cells (the boundary is comparator-dependent), so they only continue
    assert padded_cell_verdict(4, 20, 0, 40) == "continue"
    assert padded_cell_verdict(9, 39, 1, 90) == "continue"


def test_d16_ladder_vs_a_clean_0_of_40_comparator():
    assert padded_cell_verdict(0, 40, 0, 40) == "contained"
    assert padded_cell_verdict(1, 40, 0, 40) == "escalate"
    assert padded_cell_verdict(1, 90, 0, 40) == "contained"
    assert padded_cell_verdict(4, 90, 0, 40) == "not_contained"


def test_d16_ladder_vs_deepseeks_1_of_90_comparator():
    assert padded_cell_verdict(0, 40, 1, 90) == "contained"
    assert padded_cell_verdict(1, 40, 1, 90) == "escalate"
    assert padded_cell_verdict(1, 90, 1, 90) == "contained"


def test_d16_ladder_is_comparator_dependent_no_fixed_cutoff():
    # the same padded count, two verdicts: 4/90 fails against a clean 0/40 comparator
    # (+10.9%) but CLEARS against deepseek's archived 1/90 (+9.8%) — why any fixed
    # futility cutoff would be wrong on one side (D16)
    assert padded_cell_verdict(4, 90, 0, 40) == "not_contained"
    assert padded_cell_verdict(4, 90, 1, 90) == "contained"


def test_d16_ladder_judges_a_short_escalation_at_what_it_has():
    # the escalation is single-shot: past N_JUDGE the cell is judged at whatever n it
    # reached (a short bank never buys a second extension)
    assert padded_cell_verdict(1, 60, 0, 40) == "contained"       # [−7.2%, +8.9%]
    assert padded_cell_verdict(4, 60, 0, 40) == "not_contained"   # +15.9%


# ── claim 2's composition (both components, both wall g; v1 = D14's own rollup) ──────

def _g2(contained: bool, separated: bool) -> dict:
    return {"contained": contained, "separated": separated}


def test_claim2_model_needs_both_components_at_both_g():
    assert claim2_model_verdict({0.1: _g2(True, True), 0.3: _g2(True, True)}) == "cleared"
    assert claim2_model_verdict({0.1: _g2(True, True), 0.3: _g2(True, False)}) == "partial"
    assert claim2_model_verdict({0.1: _g2(False, True), 0.3: _g2(True, True)}) == "partial"
    assert claim2_model_verdict({0.1: _g2(True, False), 0.3: _g2(False, True)}) == "not_cleared"
    assert claim2_model_verdict({0.1: _g2(False, False), 0.3: _g2(False, False)}) == "not_cleared"


def test_claim2_v1_rollup_is_d14s_imported_not_redefined():
    assert m2.claim2_v1_verdict is m1.claim1_v1_verdict


# ── claim 3's counter and gate (the rule committed blind, D17) ───────────────────────

def test_emission_split_counts_the_committed_rule():
    rows = ([{"outcome": "emit_attractor"}] * 5 + [{"outcome": "emit_other_wrong"}] * 2
            + [{"outcome": "abstain"}] * 3 + [{"outcome": "reclaimed"}] * 1)
    assert emission_split(rows) == {"n": 11, "wrong": 7, "attractor": 5,
                                    "other_wrong": 2, "abstain": 3, "reclaimed": 1}


def test_claim3_gate_excludes_zero_on_the_emission_gap():
    # orientation (stats.py convention): base=blank, mech=lossy → d = lossy − blank
    v = claim3_verdict(82, 90, 0, 40)          # the probe-strength gap clears
    assert v["cleared"] is True
    assert v["d"] == pytest.approx(82 / 90)
    v = claim3_verdict(2, 90, 0, 40)           # indistinguishable at this n: no claim
    assert v["cleared"] is False


# ── protocol facts the new cells lean on ─────────────────────────────────────────────

def test_source_first_notes_are_replicates_across_knob_gs():
    # sf@0.6 and sf@1.0 are the IDENTICAL note string (the g mapping is a threshold):
    # a free replicate pair, given M1's same agreement check in m2's judge
    p = bank_problem(0, 0)
    assert memory_note(p, 0.6, "source_first") == memory_note(p, 1.0, "source_first")
    # the blank note is g-independent by construction
    assert memory_note(p, 0.1, "blank") == memory_note(p, 1.0, "blank")


# ── the grid runner (over M1's banks, on fakes) ──────────────────────────────────────

def _grid_rows(root, key):
    return [json.loads(l) for l in
            (root / f"m2-grid-{key}" / "results.jsonl").read_text().splitlines()]


def test_load_trajectory_reads_the_bank_trial_file(tmp_path):
    run_bank(m2_factory(), target=2, seed=0, runs_root=tmp_path,
             models={"fakea": FAKES["fakea"]})
    traj = load_trajectory(tmp_path, "fakea", 1)
    assert len(traj) == 19                     # [system, plant, a] + 8 × (user, a)
    assert traj[0]["role"] == "system" and traj[-1]["role"] == "assistant"
    p = bank_problem(0, 1)
    assert any(p.question in m["content"] for m in traj)   # the source travels with it


def test_run_grid_runs_the_cell_plan_in_bank_order(tmp_path):
    run_bank(m2_factory(), target=3, seed=0, runs_root=tmp_path, models=FAKES)
    res = run_grid(m2_factory(), n=2, seed=0, runs_root=tmp_path, models=FAKES,
                   blank_models=("fakea",))
    rows_a, rows_b = _grid_rows(tmp_path, "fakea"), _grid_rows(tmp_path, "fakeb")
    assert len(rows_a) == 2 * 7 and len(rows_b) == 2 * 6   # blank ran on fakea only
    assert {(r["policy"], r["g"]) for r in rows_a} == set(
        m2.cell_plan("fakea", blank_models=("fakea",)))
    for r in rows_a:
        assert r["outcome"] in OUTCOMES
        assert "temperature" in r and "pid" in r and "cost" in r
        assert r["wrong"] == (r["outcome"] in ("emit_attractor", "emit_other_wrong"))
        p = bank_problem(0, r["bank_trial"])
        if r["policy"] == "lossy" and r["g"] == 1.0:
            # the transcript cell: no note travels; the full session-1 trajectory does
            assert r["note"] is None and r["transcript_turns"] == 19
        else:
            assert "(Memory of an earlier session.)" in r["note"]
            # the per-trial source gate held in the right direction
            assert source_present(r["note"], p) == expected_source_presence(
                r["policy"], r["g"])
    # the M2WallFake wall: source in context (knob cells, transcript included)
    # reclaims; padded and blank (source absent) never do
    for r in rows_a:
        if r["policy"] in ("lossy_padded", "blank"):
            assert not r["reclaimed"] and r["outcome"] == "abstain"
        else:
            assert r["reclaimed"]
    assert res["fakea"]["cells"]["blank@0.1"]["n"] == 2
    assert res["fakeb"]["cells"].get("blank@0.1") is None


def test_run_grid_extends_without_duplicates(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(m2_factory(), target=4, seed=0, runs_root=tmp_path, models=models)
    run_grid(m2_factory(), n=2, seed=0, runs_root=tmp_path, models=models,
             blank_models=("fakea",))
    run_grid(m2_factory(), n=4, seed=0, runs_root=tmp_path, models=models,
             blank_models=("fakea",))
    rows = _grid_rows(tmp_path, "fakea")
    for policy, g in m2.cell_plan("fakea", blank_models=("fakea",)):
        cell = [r["bank_trial"] for r in rows if r["policy"] == policy and r["g"] == g]
        assert cell == [0, 1, 2, 3]            # bank order, extended once, no dupes


def test_run_grid_caps_knob_and_blank_but_ladders_padded(tmp_path):
    # knob and blank cells are FIXED at N_JUDGE (D18/D17) — only padded cells follow
    # the ladder past it; the caps are exercised at small stand-in values
    models = {"fakea": FAKES["fakea"]}
    run_bank(m2_factory(), target=5, seed=0, runs_root=tmp_path, models=models)
    run_grid(m2_factory(), n=5, seed=0, runs_root=tmp_path, models=models,
             blank_models=("fakea",), knob_cap=3)
    rows = _grid_rows(tmp_path, "fakea")
    for policy, g in m2.cell_plan("fakea", blank_models=("fakea",)):
        cell = [r for r in rows if r["policy"] == policy and r["g"] == g]
        assert len(cell) == (5 if policy == "lossy_padded" else 3), (policy, g)


def test_run_grid_is_honest_when_the_bank_runs_short(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(m2_factory(), target=2, seed=0, runs_root=tmp_path, models=models)
    res = run_grid(m2_factory(), n=4, seed=0, runs_root=tmp_path, models=models,
                   blank_models=("fakea",))
    assert res["fakea"]["short"]
    assert all(c["n"] == 2 for c in res["fakea"]["cells"].values())


# ── the checkpoint (counts + hand-read sample; NO futility — D16) ────────────────────

def _write_rows(root, dirname, cells):
    """cells: {(policy, g): [outcome, ...]} — synthetic logged rows (judge/checkpoint
    are pure functions of the JSONLs, nothing else)."""
    d = root / dirname
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "results.jsonl", "w", encoding="utf-8") as f:
        for (policy, g), outcomes in cells.items():
            for i, outcome in enumerate(outcomes):
                f.write(json.dumps({
                    "bank_trial": i, "pid": f"m1g0-{i:02d}", "policy": policy, "g": g,
                    "note": "(Memory of an earlier session.) synthetic",
                    "reply": "ANSWER: 0", "parsed": 0.0, "hedged": False,
                    "outcome": outcome, "reclaimed": outcome == "reclaimed",
                    "model": "fake", "temperature": 0.0}) + "\n")


def _reclaims(k: int, n: int) -> list[str]:
    return ["reclaimed"] * k + ["abstain"] * (n - k)


def test_checkpoint_counts_and_samples_without_futility(tmp_path):
    _write_rows(tmp_path, "m2-grid-fakea", {
        ("lossy_padded", 0.1): _reclaims(4, 20),   # 4 strays: futile under D14, not here
        ("blank", 0.1): ["abstain"] * 20,
    })
    out = m2.checkpoint(tmp_path, {"fakea": FAKES["fakea"]}, sample_k=3, rng_seed=0)
    cells = out["fakea"]["cells"]
    assert cells["lossy_padded@0.1"]["k"] == 4 and cells["lossy_padded@0.1"]["n"] == 20
    assert cells["blank@0.1"]["k"] == 0
    for cell in cells.values():
        assert "futile" not in cell            # no reclaim ceiling on any M2 cell
        pids = [r["pid"] for r in cell["sample"]]
        assert len(pids) == 3 and len(set(pids)) == 3   # ≥3 distinct trials to read
    assert "futile_cells" not in out["fakea"]


# ── the judge (pure function of the m1 + m2 logged rows) ─────────────────────────────

_CLEAN_M1 = {
    ("lossy", 0.1): _reclaims(0, 40), ("lossy", 0.3): _reclaims(0, 40),
    ("source_first", 0.1): _reclaims(40, 40), ("source_first", 0.3): _reclaims(40, 40),
}

_CLEAN_M2 = {
    ("lossy_padded", 0.1): _reclaims(0, 40), ("lossy_padded", 0.3): _reclaims(0, 40),
    ("lossy", 0.6): _reclaims(38, 40), ("lossy", 1.0): _reclaims(40, 40),
    ("source_first", 0.6): _reclaims(40, 40), ("source_first", 1.0): _reclaims(39, 40),
}


def test_judge_clears_claim2_and_claim3_on_clean_cells(tmp_path):
    # deepseek-shaped comparator: lossy@0.1 at n=90 with its emission split UNTALLIED
    # until now — the judge counts it from the rows, at judge time (the no-peek rule)
    _write_rows(tmp_path, "m1-grid-fakea", {
        **_CLEAN_M1,
        ("lossy", 0.1): ["emit_attractor"] * 80 + ["emit_other_wrong"] * 2
                        + ["abstain"] * 8,
    })
    _write_rows(tmp_path, "m2-grid-fakea", {
        **_CLEAN_M2, ("blank", 0.1): ["abstain"] * 40,
    })
    out = m2.judge(tmp_path, {"fakea": FAKES["fakea"]})
    m = out["models"]["fakea"]
    for g in ("0.1", "0.3"):
        pg = m["claim2"]["per_g"][g]
        assert pg["equivalence"]["verdict"] == "contained"
        assert pg["contained"] and pg["separated"] and pg["passes"]
    # separation orientation: d = source_first − lossy_padded = +1.0 on clean cells
    assert m["claim2"]["per_g"]["0.1"]["separation"]["d"] == pytest.approx(1.0)
    assert m["claim2"]["verdict"] == "cleared"
    assert out["claim2_v1"] == "partial"       # one cleared model of one is not two
    c3 = m["claim3"]
    assert c3["lossy"] == {"n": 90, "wrong": 82, "attractor": 80, "other_wrong": 2,
                           "abstain": 8, "reclaimed": 0}
    assert c3["blank"] == {"n": 40, "wrong": 0, "attractor": 0, "other_wrong": 0,
                           "abstain": 40, "reclaimed": 0}
    assert c3["cleared"] is True and c3["d"] == pytest.approx(82 / 90)
    assert m["replicate"]["consistent"] is True         # sf@0.6 vs sf@1.0
    # the merged cell table the knob figure draws from: m1 wall + m2 fills
    assert m["cells"]["lossy@0.1"]["n"] == 90 and m["cells"]["lossy@0.6"]["n"] == 40
    assert m["cells"]["lossy_padded@0.1"]["wilson_hi"] < 0.10
    assert m["cells"]["blank@0.1"]["rate"] == 0.0


def test_judge_reports_escalate_as_unheld_and_partial(tmp_path):
    _write_rows(tmp_path, "m1-grid-fakea", _CLEAN_M1)
    _write_rows(tmp_path, "m2-grid-fakea", {
        ("lossy_padded", 0.1): _reclaims(1, 40),   # a single stray at 40 → escalate
        ("lossy_padded", 0.3): _reclaims(0, 40),
    })
    m = m2.judge(tmp_path, {"fakea": FAKES["fakea"]})["models"]["fakea"]
    pg = m["claim2"]["per_g"]["0.1"]
    assert pg["equivalence"]["verdict"] == "escalate"
    assert pg["equivalence"]["d"] == pytest.approx(0.025)
    assert not pg["contained"] and not pg["passes"]     # escalate ≠ contained
    assert m["claim2"]["per_g"]["0.3"]["passes"]
    assert m["claim2"]["verdict"] == "partial"
    assert m["claim3"] is None                 # no blank rows → no claim-3 verdict
    assert m["replicate"] is None              # no knob sf cells logged yet


def test_judge_fails_claim2_and_nulls_claim3_honestly(tmp_path):
    _write_rows(tmp_path, "m1-grid-fakea", {
        **_CLEAN_M1,
        ("lossy", 0.1): ["emit_attractor"] * 2 + ["abstain"] * 88,   # a near-null split
    })
    _write_rows(tmp_path, "m2-grid-fakea", {
        ("lossy_padded", 0.1): _reclaims(4, 90),   # +10.9% vs 0/40: not contained
        ("lossy_padded", 0.3): _reclaims(4, 90),
        ("blank", 0.1): ["abstain"] * 40,
    })
    m = m2.judge(tmp_path, {"fakea": FAKES["fakea"]})["models"]["fakea"]
    for g in ("0.1", "0.3"):
        pg = m["claim2"]["per_g"][g]
        assert pg["equivalence"]["verdict"] == "not_contained"
        assert pg["separated"]                 # sf still beats padded …
        assert not pg["passes"]                # … but equivalence failed: AND semantics
    assert m["claim2"]["verdict"] == "not_cleared"
    assert m["claim3"]["cleared"] is False     # 2/90 vs 0/40 straddles zero: no claim
    assert m["claim3"]["lossy"]["wrong"] == 2


def test_judge_two_cleared_models_clear_claim2_v1(tmp_path):
    for key in FAKES:
        _write_rows(tmp_path, f"m1-grid-{key}", _CLEAN_M1)
        _write_rows(tmp_path, f"m2-grid-{key}", _CLEAN_M2)
    out = m2.judge(tmp_path, FAKES)
    assert out["claim2_v1"] == "cleared"


# ── the figures ──────────────────────────────────────────────────────────────────────

def _judged_clean(tmp_path):
    _write_rows(tmp_path, "m1-grid-fakea", {
        **_CLEAN_M1,
        ("lossy", 0.1): ["emit_attractor"] * 82 + ["abstain"] * 8,
    })
    _write_rows(tmp_path, "m2-grid-fakea", {**_CLEAN_M2, ("blank", 0.1): ["abstain"] * 40})
    return m2.judge(tmp_path, {"fakea": FAKES["fakea"]})


def test_make_knob_figure_writes_the_png(tmp_path):
    out = _judged_clean(tmp_path)
    path = tmp_path / "figs" / "m2-knob.png"
    make_knob_figure(out, path)
    assert path.exists() and path.stat().st_size > 0


def test_make_emission_figure_writes_the_png(tmp_path):
    out = _judged_clean(tmp_path)
    path = tmp_path / "figs" / "m2-emission.png"
    make_emission_figure(out, path)
    assert path.exists() and path.stat().st_size > 0
