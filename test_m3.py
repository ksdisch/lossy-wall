"""test_m3.py — the M3 cross-check machinery's free-testable parts. No network, no cost.

What's pinned here, before the oracle run produces its first row (the D14/D16 pattern —
the verdict rule lives in code before any data exists):
  - the agreement criterion EXACTLY as pre-committed in docs/M3-BRIEF.md: per gated
    overlap cell (llama · directed · {lossy, lossy_padded, source_first} × g ∈
    {0.1, 0.3}), the Newcombe 95% interval on (their rate − our archived rate), our
    stats.py, unequal n; AGREE iff every interval contains zero, else DISCREPANT naming
    the cell(s). The brief's boundary arithmetic is asserted AT ITS PUBLISHED VALUES,
    not re-derived: 0/96 vs 0/40 → [−8.8%, +3.8%]; 4/96 → [−5.0%, +10.2%]; even 8/96 →
    [−1.3%, +15.6%] (all consistent — the criterion tolerates provider noise); sf
    92/96 vs 40/40 → [−10.2%, +5.0%] consistent; sf 84/96 vs 40/40 → [−20.6%, −2.3%]
    FIRES — the gate ignores noise and catches structure;
  - the judge's readiness guard: nothing is judged below the full paper economy
    (n=96/cell, D19-A); the seed-1 checkpoint has recount-and-eyes powers only;
  - their fix_*.jsonl reader and the recount (per-cell k/n both arms, seed/pid
    bookkeeping, completeness = every cell n equals pids × seeds);
  - the spot-check's consistency rule, THEIR score re-typed (numeric: parsed answer
    within 0.5 of truth — experiment.py::score), applied per sampled row to their
    logged answer/correct pair against the problems' known truth/drift values;
  - the archived llama comparators recounted from evidence/ (0/40, 0/40, 0/40, 0/40,
    40/40, 40/40 — the judged-once record the criterion compares against);
  - the D20 rider-a recount: structure only (n=40 per model, split identities) — the
    VALUES are deliberately not pinned here; they are counted once, at table time;
  - the paper constants as their README/NOTE_parser_fix.md state them (the free
    extraction task confirms against the arXiv v2 HTML before the table ships);
  - the comparison table's labels (method / n / temperature / problem economy / arm,
    the two protocol findings, the fixture line, qwen's no-comparable-cell label) and
    the capstone figure (docs/figs/capstone.png; milestone figures stay frozen, D22).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import bootstrap
import m0
import m1
import m2
import m3
from grader import ABSTAIN, EMIT_ATTRACTOR, EMIT_OTHER, RECLAIMED
from m3 import (agreement_judge, comparison_table, judge_ready, make_capstone,
                oracle_cells, our_cells, read_fix_rows, recount, rider_a_recount,
                spot_check)

WALL_POLICIES = ("lossy", "lossy_padded", "source_first")


# ── constants: the run's economy, the gated set, the frozen figure paths ─────────────

def test_the_oracle_constants():
    assert m3.N_ORACLE == 96                      # 32 problems × 3 seeds (D19-A)
    assert m3.GATED_G == bootstrap.GATED_G == (0.1, 0.3)
    assert set(m3.GATED_CELLS) == {(p, g) for p in WALL_POLICIES for g in (0.1, 0.3)}
    assert len(m3.GATED_CELLS) == 6
    assert m3.DEFAULT_ORACLE_CKPT.name == "fix_meta-llama_llama-3.1-8b-instruct_arith.jsonl"
    assert m3.OUR_TEMP is m0.TEMPERATURE          # D10; their tool default matches


def test_capstone_is_a_new_file_and_the_milestone_figures_stay_frozen():
    assert m3.CAPSTONE_PATH == Path("docs/figs/capstone.png")
    assert m1.FIGURE_PATH == Path("docs/figs/m1-wall.png")
    assert m2.KNOB_FIGURE_PATH == Path("docs/figs/m2-knob.png")
    assert m2.EMISSION_FIGURE_PATH == Path("docs/figs/m2-emission.png")


# ── their checkpoint reader and the recount ──────────────────────────────────────────

TRUTHS = {"a1": {"correct": 197.0, "drift": 176.0},
          "a2": {"correct": 55.0, "drift": 76.0}}


def _oracle_row(pid, g, arm, policy, answer, correct, seed=0):
    return {"pid": pid, "integrity": g, "arm": arm, "policy": policy,
            "answer": answer, "correct": correct, "seed": seed,
            "model": "meta-llama/llama-3.1-8b-instruct_arith"}


def _oracle_file(tmp_path, pids=("a1", "a2"), seeds=(0,)) -> Path:
    """A tiny complete checkpoint: every (seed, pid, policy) unit contributes all four
    integrities × both arms, source_first correct everywhere, lossy/padded correct
    only above the wall — the shape their runner writes. A correct row carries the
    pid's OWN truth value (TRUTHS), so the file is internally consistent by
    construction and the spot-check's happy path is real."""
    path = tmp_path / "fix_test_arith.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n")                                        # blank lines tolerated
        for s in seeds:
            for pid in pids:
                truth = TRUTHS.get(pid, {}).get("correct", 197.0)
                for policy in WALL_POLICIES:
                    for g in (1.0, 0.6, 0.3, 0.1):
                        for arm in ("generic", "directed"):
                            ok = policy == "source_first" or g >= 0.6
                            f.write(json.dumps(_oracle_row(
                                pid, g, arm, policy, truth if ok else None, ok,
                                seed=s)) + "\n")
        f.write("\n")
    return path


def test_read_fix_rows_reads_their_schema_and_rejects_missing_keys(tmp_path):
    path = _oracle_file(tmp_path)
    rows = read_fix_rows(path)
    assert len(rows) == 2 * 3 * 4 * 2
    assert {"pid", "integrity", "arm", "policy", "answer", "correct", "seed"} <= set(rows[0])
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"pid": "x", "arm": "directed"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        read_fix_rows(bad)


def test_oracle_cells_groups_the_directed_arm_only(tmp_path):
    rows = read_fix_rows(_oracle_file(tmp_path, pids=("a1", "a2", "a3"), seeds=(0, 1)))
    cells = oracle_cells(rows)
    assert set(cells) == {(p, g) for p in WALL_POLICIES for g in (1.0, 0.6, 0.3, 0.1)}
    assert cells[("lossy", 0.1)] == [0] * 6                  # 3 pids × 2 seeds
    assert cells[("source_first", 0.1)] == [1] * 6
    generic = oracle_cells(rows, arm="generic")
    assert generic[("source_first", 0.3)] == [1] * 6


def test_recount_bookkeeping_and_completeness(tmp_path):
    rows = read_fix_rows(_oracle_file(tmp_path, pids=("a1", "a2"), seeds=(0, 1, 2)))
    out = recount(rows)
    assert out["pids"] == 2 and out["seeds"] == [0, 1, 2]
    assert out["units"] == 2 * 3 * 3                         # seed × pid × policy
    assert out["complete"] is True
    cell = out["cells"][("lossy", 0.1, "directed")]
    assert (cell["k"], cell["n"]) == (0, 6)
    assert out["cells"][("source_first", 1.0, "generic")]["rate"] == 1.0
    # drop one row → the touched cell no longer matches pids × seeds
    out2 = recount(rows[:-1])
    assert out2["complete"] is False


# ── the agreement criterion — the brief's boundary table, asserted not re-derived ────

OURS_LLAMA = {("lossy", 0.1): (0, 40), ("lossy", 0.3): (0, 40),
              ("lossy_padded", 0.1): (0, 40), ("lossy_padded", 0.3): (0, 40),
              ("source_first", 0.1): (40, 40), ("source_first", 0.3): (40, 40)}


def _theirs(sf01=(96, 96), sf03=(92, 96), lossy01=(0, 96), lossy03=(0, 96),
            pad01=(0, 96), pad03=(0, 96)):
    return {("lossy", 0.1): lossy01, ("lossy", 0.3): lossy03,
            ("lossy_padded", 0.1): pad01, ("lossy_padded", 0.3): pad03,
            ("source_first", 0.1): sf01, ("source_first", 0.3): sf03}


def test_agreement_boundaries_exactly_as_published_in_the_brief():
    out = agreement_judge(_theirs(), OURS_LLAMA)
    c = out["cells"]
    lo, hi = c[("lossy", 0.1)]["lo"], c[("lossy", 0.1)]["hi"]      # 0/96 vs 0/40
    assert lo == pytest.approx(-0.088, abs=5e-4)
    assert hi == pytest.approx(+0.038, abs=5e-4)
    lo, hi = c[("source_first", 0.3)]["lo"], c[("source_first", 0.3)]["hi"]  # 92/96 vs 40/40
    assert lo == pytest.approx(-0.102, abs=5e-4)
    assert hi == pytest.approx(+0.050, abs=5e-4)
    assert out["verdict"] == "AGREE" and out["discrepant"] == []


def test_the_criterion_tolerates_stray_recoveries_at_the_extremes():
    out4 = agreement_judge(_theirs(lossy01=(4, 96)), OURS_LLAMA)
    cell = out4["cells"][("lossy", 0.1)]
    assert cell["lo"] == pytest.approx(-0.050, abs=5e-4)
    assert cell["hi"] == pytest.approx(+0.102, abs=5e-4)
    out8 = agreement_judge(_theirs(lossy01=(8, 96)), OURS_LLAMA)
    cell = out8["cells"][("lossy", 0.1)]
    assert cell["lo"] == pytest.approx(-0.013, abs=5e-4)
    assert cell["hi"] == pytest.approx(+0.156, abs=5e-4)
    assert out4["verdict"] == out8["verdict"] == "AGREE"


def test_the_criterion_fires_on_structure_a_12_point_sf_drop():
    out = agreement_judge(_theirs(sf01=(84, 96)), OURS_LLAMA)
    cell = out["cells"][("source_first", 0.1)]
    assert cell["lo"] == pytest.approx(-0.206, abs=5e-4)
    assert cell["hi"] == pytest.approx(-0.023, abs=5e-4)
    assert cell["consistent"] is False
    assert out["verdict"] == "DISCREPANT"
    assert out["discrepant"] == ["source_first@0.1"]


def test_d_is_theirs_minus_ours():
    out = agreement_judge(_theirs(sf03=(84, 96)), OURS_LLAMA)
    assert out["cells"][("source_first", 0.3)]["d"] == pytest.approx(84 / 96 - 1.0)


def test_judge_ready_requires_the_full_paper_economy_on_every_gated_cell():
    full = {cell: [1] * 96 for cell in m3.GATED_CELLS}
    assert judge_ready(full) is True
    smoke = {cell: [1] * 32 for cell in m3.GATED_CELLS}      # the seed-1 stage
    assert judge_ready(smoke) is False
    missing = {cell: [1] * 96 for cell in m3.GATED_CELLS[:-1]}
    assert judge_ready(missing) is False


# ── the archived comparators, recounted through the real evidence path ───────────────

def test_our_cells_pins_the_judged_llama_record():
    cells = our_cells("llama")
    for policy in ("lossy", "lossy_padded"):
        for g in (0.1, 0.3):
            assert cells[(policy, g)] == (0, 40)
    for g in (0.1, 0.3):
        assert cells[("source_first", g)] == (40, 40)
    # the knob descriptives ride along for the table (D18's committed record)
    assert cells[("lossy", 0.6)] == (38, 40)
    assert cells[("lossy", 1.0)] == (28, 40)
    assert cells[("source_first", 0.6)] == (27, 40)
    assert cells[("source_first", 1.0)] == (26, 40)


# ── the spot-check: their score rule re-typed, applied to their logged pairs ─────────

def test_spot_check_consistent_rows_pass(tmp_path):
    rows = read_fix_rows(_oracle_file(tmp_path))
    out = spot_check(rows, TRUTHS, k=3)
    assert out["all_consistent"] is True
    assert {r["policy"] for r in out["records"]} == set(WALL_POLICIES)
    for policy in WALL_POLICIES:                             # ≥3 rows per policy
        assert sum(r["policy"] == policy for r in out["records"]) == 3


def test_spot_check_catches_a_correct_flag_that_contradicts_the_answer(tmp_path):
    rows = read_fix_rows(_oracle_file(tmp_path))
    rows.append(_oracle_row("a2", 0.1, "directed", "lossy", 999.0, True))
    out = spot_check(rows, TRUTHS, k=200)                    # k big: sample everything
    bad = [r for r in out["records"] if not r["consistent"]]
    assert out["all_consistent"] is False
    assert len(bad) == 1 and bad[0]["answer"] == 999.0 and bad[0]["correct"] is True


def test_spot_check_annotates_the_inherited_attractor(tmp_path):
    rows = [_oracle_row("a1", 0.1, "directed", "lossy", 176.0, False),
            _oracle_row("a1", 0.1, "directed", "source_first", 197.0, True),
            _oracle_row("a1", 0.1, "directed", "lossy_padded", None, False)]
    out = spot_check(rows, TRUTHS, k=5)
    by = {r["policy"]: r for r in out["records"]}
    assert by["lossy"]["is_attractor"] is True               # emitted the planted drift
    assert by["lossy"]["consistent"] is True                 # wrong answer, flag False: coherent
    assert by["source_first"]["is_attractor"] is False
    assert by["lossy_padded"]["answer"] is None              # their abstention convention


def test_spot_check_is_deterministic(tmp_path):
    rows = read_fix_rows(_oracle_file(tmp_path, pids=("a1", "a2"), seeds=(0, 1)))
    a = spot_check(rows, TRUTHS, k=3)
    b = spot_check(rows, TRUTHS, k=3)
    assert a == b


# ── the D20 rider-a recount: structure only — the values are counted at table time ───

def test_rider_a_recount_shape_without_tallying_here():
    out = rider_a_recount()
    assert set(out) == {"llama", "qwen72b"}
    for split in out.values():
        assert split["n"] == 40                              # archived lossy@0.1 rows
        assert split["wrong"] == split["attractor"] + split["other_wrong"]
        assert split["wrong"] + split["abstain"] + split["reclaimed"] == split["n"]


# ── the paper constants, pinned to the arXiv v2 extraction (evidence/m3/) ────────────
# The brief drafted these from the repo README; the extraction against the paper found
# a last-digit variance on three cells (paper 0.01 / 0.99 / 0.99 vs README 0.00 /
# 0.96 / 1.00) and pinned the paper's stated temperature (0.7). The paper's committed
# values win the paper column; the README variant stays as the footnoted variance.

def test_paper_constants_match_the_arxiv_v2_extraction():
    w = m3.PAPER["wall_llama"]                    # (point, ci_lo, ci_hi), verbatim
    assert w[("lossy", 0.3)] == (0.01, 0.00, 0.03)
    assert w[("lossy", 0.1)] == (0.00, 0.00, 0.00)
    assert w[("lossy_padded", 0.3)] == (0.00, 0.00, 0.00)
    assert w[("lossy_padded", 0.1)] == (0.00, 0.00, 0.00)
    assert w[("source_first", 0.3)] == (0.99, 0.97, 1.00)
    assert w[("source_first", 0.1)] == (0.99, 0.97, 1.00)
    assert w[("lossy", 1.0)] == (0.61, 0.52, 0.71)           # the knob rows ride along
    assert m3.PAPER["wall_n"] == 96
    assert m3.PAPER["wall_temp"] == 0.7           # the paper's caption, verbatim; the
    assert m3.OUR_TEMP == 0.0                     # tool default = our D10 stays matched
    assert m3.PAPER["readme_wall_llama"][("source_first", 0.3)] == 0.96
    d = m3.PAPER["disposition_delta"]                        # post-v2 corrected values
    assert d["deepseek-chat"] == 0.83 and d["qwen-2.5-7b"] == 0.39
    assert d["llama-3.1-8b"] == 0.17 and d["frontier"] == 0.00
    assert m3.PAPER["blank_lossy_emit_llama"] == 0.17
    assert m3.OUR_PROBE == {"llama": (1, 12, 0, 12), "qwen72b": (0, 12, 0, 12)}


# ── the comparison table: every column labeled, every footnote present ───────────────

def test_comparison_table_labels_rows_and_footnotes(tmp_path):
    theirs = {(p, g): ([1] * 96 if p == "source_first" else [0] * 96)
              for p in WALL_POLICIES for g in (1.0, 0.6, 0.3, 0.1)}
    text = comparison_table(theirs, fixture_line="their parse_answer read 0/8 escaped"
                                                 " ANSWER lines (ours: 8/8)")
    for marker in ("paper-committed", "their-harness-run", "ours",
                   "method", "temperature", "problem economy", "directed",
                   "gated", "descriptive",
                   "reproduce_tables.py", "empty data/results",
                   "may under-read escaped commits as abstentions",
                   "no comparable cell", "qwen-2.5-72b", "10×",
                   "their parse_answer read 0/8"):
        assert marker in text, marker
    assert "+58%" in text                                    # our judged deepseek gap
    assert "+0.83" in text                                   # their disposition delta
    assert "0.99 B[0.97, 1.00]" in text                      # the paper's sf cells, brackets verbatim
    assert "temperature 0.7" in text                         # the paper column's label
    assert "records the variance" in text                    # the paper-vs-README footnote
    assert "[+44.2%, +67.5%]" in text                        # our judged claim-3 interval
    assert "contains their value" in text                    # the llama probe concordance


def test_comparison_table_pending_fixture_line(tmp_path):
    theirs = {(p, g): [0] * 8 for p in WALL_POLICIES for g in (0.3, 0.1)}
    text = comparison_table(theirs, fixture_line=None)
    assert "fixture check: pending" in text


# ── the capstone figure ──────────────────────────────────────────────────────────────

def test_make_capstone_writes_one_png(tmp_path):
    ours_by_model = {key: dict(our_cells(key)) for key in ("llama", "deepseek", "qwen72b")}
    emission = {"lossy": {"n": 90, "wrong": 52, "attractor": 33, "other_wrong": 19,
                          "abstain": 37, "reclaimed": 1},
                "blank": {"n": 40, "wrong": 0, "attractor": 0, "other_wrong": 0,
                          "abstain": 40, "reclaimed": 0}}
    oracle = {(p, g): ((96, 96) if p == "source_first" else (0, 96))
              for p in WALL_POLICIES for g in (0.1, 0.3)}
    path = tmp_path / "figs" / "capstone.png"
    make_capstone(ours_by_model, emission, oracle, path)
    assert path.exists() and path.stat().st_size > 0
