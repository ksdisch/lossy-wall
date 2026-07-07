"""test_m1.py — the M1 grid driver's free-testable parts. No network, no cost.

What's pinned here, before any paid call (m0.py's D8/D9 pattern — verdicts
pre-committed in code so they can't bend after data arrives):
  - the D14 ladder EXACTLY as recorded in DECISIONS.md: nothing clears at the N=20
    checkpoint; the 0.10 ceiling on the Wilson upper bound judged at N=40; the single
    pre-committed escalation to N≈90; ≥4 reclaims final anywhere — with the boundary
    arithmetic (0/20 → 16.1%, 0/40 → 8.8%, 3/90 → 9.3%, 4/90 → 10.9%) asserted, not
    assumed;
  - claim 1's composition: a model clears only if BOTH components (ceiling + positive
    Newcombe gap) hold at BOTH g ∈ {0.1, 0.3}; v1 needs ≥2 cleared models;
  - the bank builder end-to-end on fakes: the fresh `m1-` schedule (shared across
    models, disjoint from M0's), resume-without-rerun, honest `short` on a
    take-starved model;
  - the grid runner end-to-end on fakes: bank-order trials, resume/extend without
    duplicates, the source_first cap at N=40 (no ceiling applies to sf, so it never
    escalates), row shapes carrying the hand-audit trail;
  - the checkpoint's mechanical half (futility + the ≥3-trial hand-read sample) and
    the judge (pure function of logged rows), including the replicate-cell sanity
    check (sf@0.1 and sf@0.3 are the same note string by the g-threshold mapping).

The WallFake is this file's hand-crank: it always takes in session 1 and, in session 2,
reclaims exactly when the source marker is present — no randomness, so cell counts are
exact (DriftFake's 5% lucky-recovery noise would make grid assertions seed-fragile).
"""
from __future__ import annotations

import json
import random

import pytest

import m0
import m1
from m1 import (CEILING, GRID_G, N_JUDGE, N_MAX, bank_problem, checkpoint,
                claim1_model_verdict, claim1_v1_verdict, judge, load_bank,
                lossy_cell_verdict, make_figure, run_bank, run_grid)
from notes import memory_note, source_present
from problems import Problem
from stats import wilson

FAKES = {"fakea": "fake/model-a", "fakeb": "fake/model-b"}


class WallFake:
    """Deterministic wall behaviour: session 1 always commits the drift (take = n/n);
    session 2 reclaims iff the recomputable source is present in context — the
    anti-rig property with the noise removed."""

    def __init__(self, problem: Problem):
        self.problem = problem

    def chat(self, messages) -> str:
        last = (messages[-1].get("content") or "").lower()
        if "recheck" in last or "wrong" in last:
            if any(self.problem.facts[:18].lower() in (m.get("content") or "").lower()
                   for m in messages):
                return f"Rechecking... ANSWER: {self.problem.correct:g}"
            return (f"I am not sure I have enough to recompute. "
                    f"ANSWER: {self.problem.drift:g}")
        return f"Using what was given, ANSWER: {self.problem.drift:g}"


class NoTakeFake:
    """Never takes in session 1 (answers an unplanted value)."""

    def __init__(self, problem: Problem):
        self.problem = problem

    def chat(self, messages) -> str:
        return "ANSWER: 0"


def wall_factory():
    return lambda slug, problem: WallFake(problem)


# ── D10: the sampling constants are m0's, never redefined ────────────────────────────

def test_d10_constants_are_imported_from_m0():
    assert m1.TEMPERATURE is m0.TEMPERATURE
    assert m1.MAX_TOKENS is m0.MAX_TOKENS
    assert m1.TEMPERATURE == 0.0 and m1.MAX_TOKENS == 600


def test_d13_roster_is_frozen():
    # D13 resolved 2026-07-06: the re-attempt completed GREEN (18/20), so the roster is
    # llama + deepseek + the 72b family substitute — frozen for the whole milestone
    assert set(m1.ROSTER) == {"llama", "deepseek", "qwen72b"}


# ── the D14 ladder (DECISIONS.md D14) — boundary arithmetic asserted, not assumed ────

def test_d14_boundary_arithmetic():
    # the numbers the ladder's tiers were derived from, pinned with our stats.py
    assert wilson(0, 20)[1] > CEILING            # 0/20 → 16.1%: nothing clears at 20
    assert wilson(0, 40)[1] <= CEILING           # 0/40 → 8.8%: clears
    assert wilson(1, 40)[1] > CEILING            # 1/40 → 12.9%: must escalate
    assert wilson(3, 90)[1] <= CEILING           # 3/90 → 9.3%: clears after escalation
    assert wilson(4, 90)[1] > CEILING            # 4/90 → 10.9%: why ≥4 is final anywhere


def test_d14_checkpoint_cannot_clear():
    assert lossy_cell_verdict(0, 20) == "continue"
    assert lossy_cell_verdict(2, 20) == "continue"   # strays at 20 only continue
    assert lossy_cell_verdict(0, 39) == "continue"   # judging starts at N_JUDGE, not before


def test_d14_judge_at_40():
    assert lossy_cell_verdict(0, N_JUDGE) == "cleared"
    assert lossy_cell_verdict(1, N_JUDGE) == "escalate"
    assert lossy_cell_verdict(3, N_JUDGE) == "escalate"
    assert lossy_cell_verdict(4, N_JUDGE) == "not_cleared"


def test_d14_final_after_escalation():
    assert lossy_cell_verdict(0, N_MAX) == "cleared"
    assert lossy_cell_verdict(3, N_MAX) == "cleared"        # 9.3% ≤ 10%
    assert lossy_cell_verdict(1, 60) == "cleared"           # short bank: 1/60 → 8.9% clears
    assert lossy_cell_verdict(3, 60) == "not_cleared"       # short bank: 3/60 → 13.7% fails
    assert lossy_cell_verdict(3, 41) == "not_cleared"       # 3/41 → 17.5%: bound fails


def test_d14_four_reclaims_is_final_anywhere():
    for n in (20, 33, N_JUDGE, 60, N_MAX):
        assert lossy_cell_verdict(4, n) == "not_cleared"
    assert lossy_cell_verdict(7, 25) == "not_cleared"


# ── claim 1's composition (both components, both g, ≥2 models) ───────────────────────

def _g(ceiling: bool, gap: bool) -> dict:
    return {"ceiling_cleared": ceiling, "gap_positive": gap}


def test_claim1_model_needs_both_components_at_both_g():
    assert claim1_model_verdict({0.1: _g(True, True), 0.3: _g(True, True)}) == "cleared"
    assert claim1_model_verdict({0.1: _g(True, True), 0.3: _g(True, False)}) == "partial"
    assert claim1_model_verdict({0.1: _g(True, True), 0.3: _g(False, True)}) == "partial"
    assert claim1_model_verdict({0.1: _g(False, True), 0.3: _g(True, False)}) == "not_cleared"
    assert claim1_model_verdict({0.1: _g(False, False), 0.3: _g(False, False)}) == "not_cleared"


def test_claim1_v1_needs_two_cleared_models():
    assert claim1_v1_verdict(["cleared", "cleared"]) == "cleared"
    assert claim1_v1_verdict(["cleared", "cleared", "partial"]) == "cleared"
    assert claim1_v1_verdict(["cleared", "partial"]) == "partial"
    assert claim1_v1_verdict(["partial", "not_cleared"]) == "not_cleared"


# ── the m1- problem schedule (D5: fresh per trial, disjoint from M0's) ───────────────

def test_bank_problem_is_deterministic_fresh_and_not_m0s():
    a1, a2 = bank_problem(0, 3), bank_problem(0, 3)
    assert a1 == a2
    assert bank_problem(0, 4) != a1
    assert a1.pid == "m1g0-03"
    assert a1 != m0.pilot_problem(0, 3)     # M0's pilot problems are not reused


def test_source_first_notes_are_replicates_across_wall_gs():
    # the quiet protocol fact the replicate check leans on: at both wall integrities
    # source_first emits the IDENTICAL note string (the g mapping is a threshold)
    p = bank_problem(0, 0)
    assert memory_note(p, 0.1, "source_first") == memory_note(p, 0.3, "source_first")
    # while the lossy side has structure: premise survives at 0.3, not at 0.1
    assert memory_note(p, 0.1, "lossy") != memory_note(p, 0.3, "lossy")


# ── the bank builder ─────────────────────────────────────────────────────────────────

def test_run_bank_reaches_target_and_logs(tmp_path):
    res = run_bank(wall_factory(), target=4, seed=0, runs_root=tmp_path, models=FAKES)
    for key in FAKES:
        arm = res[key]
        assert (arm["takes"], arm["trials"], arm["short"]) == (4, 4, False)
        rows = [json.loads(l) for l in
                (tmp_path / f"m1-bank-{key}" / "results.jsonl").read_text().splitlines()]
        assert len(rows) == 4
        for i, row in enumerate(rows):
            assert row["trial"] == i and row["took"] is True
            assert row["pid"] == f"m1g0-{i:02d}"
            Problem(**row["problem"])       # the grid reconstructs problems from rows
            traj = (tmp_path / f"m1-bank-{key}" / f"trial-{i:02d}.jsonl").read_text()
            assert len(traj.splitlines()) == 19   # [system, plant, a] + 8 × (user, a)
    # paired design: both models saw the SAME schedule
    pids = {k: [json.loads(l)["pid"] for l in
                (tmp_path / f"m1-bank-{k}" / "results.jsonl").read_text().splitlines()]
            for k in FAKES}
    assert pids["fakea"] == pids["fakeb"]


def test_run_bank_resumes_without_rerunning(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(wall_factory(), target=3, seed=0, runs_root=tmp_path, models=models)
    first = (tmp_path / "m1-bank-fakea" / "results.jsonl").read_text()
    res = run_bank(wall_factory(), target=5, seed=0, runs_root=tmp_path, models=models)
    assert (res["fakea"]["takes"], res["fakea"]["trials"]) == (5, 5)
    text = (tmp_path / "m1-bank-fakea" / "results.jsonl").read_text()
    assert text.startswith(first)           # the original rows are untouched (a durable asset)
    pids = [json.loads(l)["pid"] for l in text.splitlines()]
    assert pids == [f"m1g0-{i:02d}" for i in range(5)]   # schedule continued, no dupes


def test_run_bank_is_honest_when_takes_starve(tmp_path):
    llm_for = lambda slug, problem: NoTakeFake(problem)   # noqa: E731
    res = run_bank(llm_for, target=3, seed=0, runs_root=tmp_path,
                   models={"fakea": FAKES["fakea"]})
    arm = res["fakea"]
    assert arm["short"] and arm["takes"] == 0
    assert arm["trials"] == 2 * 3 + 8       # the budget cap: never loops forever


def test_load_bank_returns_taken_entries_in_schedule_order(tmp_path):
    class TakeEveryOther(WallFake):
        def chat(self, messages) -> str:
            if int(self.problem.pid.split("-")[1]) % 2:
                return "ANSWER: 0"          # odd trials never take
            return super().chat(messages)

    llm_for = lambda slug, problem: TakeEveryOther(problem)   # noqa: E731
    run_bank(llm_for, target=3, seed=0, runs_root=tmp_path,
             models={"fakea": FAKES["fakea"]})
    entries = load_bank(tmp_path, "fakea", seed=0)
    assert [t for t, _ in entries] == [0, 2, 4]
    assert all(isinstance(p, Problem) for _, p in entries)
    with pytest.raises(ValueError, match="different seed"):
        load_bank(tmp_path, "fakea", seed=9)


# ── the grid runner ──────────────────────────────────────────────────────────────────

def _grid_rows(root, key):
    return [json.loads(l) for l in
            (root / f"m1-grid-{key}" / "results.jsonl").read_text().splitlines()]


def test_run_grid_runs_cells_in_bank_order_and_logs(tmp_path):
    run_bank(wall_factory(), target=3, seed=0, runs_root=tmp_path, models=FAKES)
    res = run_grid(wall_factory(), n=2, seed=0, runs_root=tmp_path, models=FAKES)
    for key in FAKES:
        rows = _grid_rows(tmp_path, key)
        assert len(rows) == 2 * len(GRID_G) * 2          # 2 trials × 2 g × 2 policies
        for r in rows:
            assert r["g"] in GRID_G
            assert r["outcome"] in ("reclaimed", "abstain", "emit_attractor",
                                    "emit_other_wrong")
            # the hand-audit trail every graded outcome carries
            assert "(Memory of an earlier session.)" in r["note"]
            assert "ANSWER:" in r["reply"]
            assert "temperature" in r and "pid" in r and "bank_trial" in r
            # the per-trial source gate held in the right direction
            p = bank_problem(0, r["bank_trial"])
            assert source_present(r["note"], p) == (r["policy"] == "source_first")
        # the WallFake wall: source_first reclaims every trial, lossy never
        for g in GRID_G:
            sf = [r for r in rows if r["policy"] == "source_first" and r["g"] == g]
            lo = [r for r in rows if r["policy"] == "lossy" and r["g"] == g]
            assert all(r["reclaimed"] for r in sf) and len(sf) == 2
            assert not any(r["reclaimed"] for r in lo) and len(lo) == 2
        assert res[key]["cells"][f"lossy@{GRID_G[0]:g}"]["n"] == 2


def test_run_grid_extends_without_duplicates(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(wall_factory(), target=4, seed=0, runs_root=tmp_path, models=models)
    run_grid(wall_factory(), n=2, seed=0, runs_root=tmp_path, models=models)
    run_grid(wall_factory(), n=4, seed=0, runs_root=tmp_path, models=models)
    rows = _grid_rows(tmp_path, "fakea")
    assert len(rows) == 4 * len(GRID_G) * 2
    for g in GRID_G:
        for policy in ("lossy", "source_first"):
            cell = [r["bank_trial"] for r in rows
                    if r["policy"] == policy and r["g"] == g]
            assert cell == [0, 1, 2, 3]      # bank order, extended once, no dupes


def test_run_grid_caps_source_first_cells(tmp_path):
    # sf has no ceiling and never escalates: D14 fixes it at N_JUDGE (=40); the cap is
    # exercised here at a small stand-in value
    models = {"fakea": FAKES["fakea"]}
    run_bank(wall_factory(), target=5, seed=0, runs_root=tmp_path, models=models)
    run_grid(wall_factory(), n=5, seed=0, runs_root=tmp_path, models=models, sf_cap=3)
    rows = _grid_rows(tmp_path, "fakea")
    for g in GRID_G:
        sf = [r for r in rows if r["policy"] == "source_first" and r["g"] == g]
        lo = [r for r in rows if r["policy"] == "lossy" and r["g"] == g]
        assert len(sf) == 3 and len(lo) == 5


def test_run_grid_is_honest_when_the_bank_runs_short(tmp_path):
    models = {"fakea": FAKES["fakea"]}
    run_bank(wall_factory(), target=2, seed=0, runs_root=tmp_path, models=models)
    res = run_grid(wall_factory(), n=4, seed=0, runs_root=tmp_path, models=models)
    arm = res["fakea"]
    assert arm["short"]
    assert all(c["n"] == 2 for c in arm["cells"].values())


# ── the checkpoint (mechanical half: futility + the hand-read sample) ────────────────

def _write_grid_rows(root, key, cells):
    """cells: {(policy, g): [outcome, ...]} — synthetic logged rows for the pure
    readers (judge/checkpoint are functions of the JSONL, nothing else)."""
    d = root / f"m1-grid-{key}"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "results.jsonl", "w", encoding="utf-8") as f:
        for (policy, g), outcomes in cells.items():
            for i, outcome in enumerate(outcomes):
                f.write(json.dumps({
                    "bank_trial": i, "pid": f"m1g0-{i:02d}", "policy": policy, "g": g,
                    "note": "(Memory of an earlier session.) synthetic",
                    "reply": "ANSWER: 0", "parsed": 0.0, "hedged": False,
                    "outcome": outcome, "reclaimed": outcome == "reclaimed",
                    "model": key, "temperature": 0.0}) + "\n")


def _outcomes(k_reclaim: int, n: int) -> list[str]:
    return ["reclaimed"] * k_reclaim + ["abstain"] * (n - k_reclaim)


def test_checkpoint_flags_futility_and_samples_for_the_hand_read(tmp_path):
    _write_grid_rows(tmp_path, "fakea", {
        ("lossy", 0.1): _outcomes(4, 20),          # ≥4 at the checkpoint: futile
        ("lossy", 0.3): _outcomes(0, 20),
        ("source_first", 0.1): _outcomes(19, 20),
        ("source_first", 0.3): _outcomes(20, 20),
    })
    out = checkpoint(tmp_path, {"fakea": FAKES["fakea"]}, sample_k=3, rng_seed=0)
    cells = out["fakea"]["cells"]
    assert cells["lossy@0.1"]["futile"] is True
    assert cells["lossy@0.3"]["futile"] is False
    assert cells["source_first@0.1"]["futile"] is False   # no ceiling on sf, ever
    for cell in cells.values():
        pids = [r["pid"] for r in cell["sample"]]
        assert len(pids) == 3 and len(set(pids)) == 3     # ≥3 distinct trials to read
    assert out["fakea"]["futile_cells"] == ["lossy@0.1"]


def test_checkpoint_sample_takes_everything_when_a_cell_is_tiny(tmp_path):
    _write_grid_rows(tmp_path, "fakea", {("lossy", 0.1): _outcomes(0, 2)})
    out = checkpoint(tmp_path, {"fakea": FAKES["fakea"]}, sample_k=3, rng_seed=0)
    assert len(out["fakea"]["cells"]["lossy@0.1"]["sample"]) == 2


# ── the judge (pure function of the logged rows) ─────────────────────────────────────

def test_judge_clears_a_clean_wall(tmp_path):
    _write_grid_rows(tmp_path, "fakea", {
        ("lossy", 0.1): _outcomes(0, 40), ("lossy", 0.3): _outcomes(0, 40),
        ("source_first", 0.1): _outcomes(40, 40), ("source_first", 0.3): _outcomes(39, 40),
    })
    out = judge(tmp_path, {"fakea": FAKES["fakea"]})
    m = out["models"]["fakea"]
    assert m["cells"]["lossy@0.1"]["verdict"] == "cleared"
    assert m["cells"]["lossy@0.3"]["verdict"] == "cleared"
    assert m["cells"]["source_first@0.1"]["verdict"] is None   # no ladder on sf
    for g in ("0.1", "0.3"):
        assert m["per_g"][g]["ceiling_cleared"] and m["per_g"][g]["gap_positive"]
    assert m["verdict"] == "cleared"
    assert m["replicate"]["consistent"] is True
    assert out["v1"] == "partial"            # one cleared model of one is not two


def test_judge_escalates_and_fails_honestly(tmp_path):
    _write_grid_rows(tmp_path, "fakea", {
        ("lossy", 0.1): _outcomes(2, 40),          # 2 strays at 40 → escalate
        ("lossy", 0.3): _outcomes(6, 40),          # ≥4 → not_cleared, final
        ("source_first", 0.1): _outcomes(40, 40),
        ("source_first", 0.3): _outcomes(40, 40),
    })
    m = judge(tmp_path, {"fakea": FAKES["fakea"]})["models"]["fakea"]
    assert m["cells"]["lossy@0.1"]["verdict"] == "escalate"
    assert m["cells"]["lossy@0.3"]["verdict"] == "not_cleared"
    assert not m["per_g"]["0.1"]["ceiling_cleared"]           # escalate ≠ cleared
    assert m["verdict"] == "not_cleared"     # gap holds but no g clears its ceiling


def test_judge_partial_when_only_one_g_passes(tmp_path):
    _write_grid_rows(tmp_path, "fakea", {
        ("lossy", 0.1): _outcomes(0, 40), ("lossy", 0.3): _outcomes(0, 40),
        ("source_first", 0.1): _outcomes(40, 40),
        ("source_first", 0.3): _outcomes(2, 40),   # gap fails at 0.3 (and flags replicate)
    })
    m = judge(tmp_path, {"fakea": FAKES["fakea"]})["models"]["fakea"]
    assert m["per_g"]["0.1"]["passes"] and not m["per_g"]["0.3"]["passes"]
    assert m["verdict"] == "partial"
    assert m["replicate"]["consistent"] is False   # two samples of one condition disagree


def test_judge_two_cleared_models_clear_v1(tmp_path):
    clean = {
        ("lossy", 0.1): _outcomes(0, 40), ("lossy", 0.3): _outcomes(0, 40),
        ("source_first", 0.1): _outcomes(40, 40), ("source_first", 0.3): _outcomes(40, 40),
    }
    _write_grid_rows(tmp_path, "fakea", clean)
    _write_grid_rows(tmp_path, "fakeb", clean)
    out = judge(tmp_path, FAKES)
    assert out["v1"] == "cleared"


# ── the figure ───────────────────────────────────────────────────────────────────────

def test_make_figure_writes_the_png(tmp_path):
    _write_grid_rows(tmp_path, "fakea", {
        ("lossy", 0.1): _outcomes(0, 40), ("lossy", 0.3): _outcomes(1, 40),
        ("source_first", 0.1): _outcomes(40, 40), ("source_first", 0.3): _outcomes(39, 40),
    })
    out = judge(tmp_path, {"fakea": FAKES["fakea"]})
    path = tmp_path / "figs" / "m1-wall.png"
    make_figure(out, path)
    assert path.exists() and path.stat().st_size > 0
