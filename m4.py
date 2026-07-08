"""m4.py — the M4 logic grid (pilot → bank → grid → checkpoint → judge → figure),
with D24's tiers and D25's soft-wall gates pre-committed in code.

M4 asks one question: does the brittle-memory effect survive a change of task? Same
two-session design as v1, second task family — constraint-deduction puzzles whose
answer is a single token from a CLOSED option set (judge-free scoring, the iron rule).
The wall is SOFT on logic (the paper's own finding): the lossy floor does not collapse
to ~0, so the v1 gates do not transfer wholesale. What D25 settles (signed 2026-07-08):

  claim 1 (the fix generalizes) — gate the GAP: the Newcombe 95% interval on
      (source_first − lossy) excludes zero at BOTH wall g, per model; ≥2 of 3 models
      clear, AND the anchored model's (llama's) soft-wall SHAPE matches the paper's
      direction. The lossy soft floor is REPORTED (Wilson CI), never gated — no lossy
      ceiling on a soft wall.
  claim 2 (content, not length) — gate SEPARATION: (source_first − lossy_padded)
      excludes zero at both g, same ≥2 bar. The padded ≈ lossy equivalence is REPORTED
      descriptively with its pre-registered caveat: δ=0.10 equivalence is unpowerable
      at hobby N on a mid-range rate (Newcombe ±0.15 at N=60 on rates ≈0.25).
  claim 3 (worse than empty) — DESCRIPTIVE in scope A (D23): the taxonomy's inherit
      fraction per lossy cell vs the abstain fraction; gated only under scope C.
  the shape read, mechanized without new constants — v1's pre-committed smallness
      scale (CEILING = 0.10, D7/D14) mirrored at both ends: a lossy floor whose Wilson
      upper bound clears the ceiling is "consistent with ~0" (the arithmetic regime —
      HARDER than the paper's logic wall → divergent); a source_first cell whose Wilson
      lower bound reaches 1 − CEILING "reaches ~1" (again the arithmetic regime).
  verdicts — REPRODUCED / PARTIAL / NULL / DISCREPANT, mapped by `m4_claim_verdict`
      before any data exists; DISCREPANT is reachable only through a scope-B
      cross-check result (not run in scope A).

Every cell is read through the four-way taxonomy (rider b, re-typed from the author's
logic_failmode.py): recov (= reclaim, what the gap counts) / inherit (the planted
drift token — the worse-than-empty signal) / novel / abst — with the CHANCE FLOOR
(~1/k for k answer options) stated per cell, so a near-baseline reclaim rate is never
over-read as re-derivation.

The paper anchor (rider a): PAPER below pins the arXiv v2 Table 6 llama·logic wall
cells from the two-pass verbatim extraction (evidence/m4/paper-extraction-logic.md).
The README artifact disagrees on every one of those cells (M3 precedent, larger here);
the PAPER values are the comparison target. No gate touches them — direction +
structure only.

The pipeline, free-before-paid (D24 gates the grid per model):

  pilot — D24: ~20 session-1 logic trajectories per model on the fresh `m4p-`
      schedule; take = the model committed the planted drift token on the take probe
      (the author's own restatement turn, D11-adapted, never carried). Tier per model
      via D8's fractions (imported, never redefined): ≥70% green / 50–70% amber
      (audit the recipe once, inflate generation by 1/t̂) / <50% trigger (the model
      sits out M4's grid; M4 proceeds on the models that take, and says so). Each
      taken trial also gets a lossy@0.1 wall read (the taxonomy) — the disposition
      probe that doubles as the claim-3-on-logic powerability read (D23-C's data).
  bank — session-1 trajectories to N_BANK = 60 TAKEN per surviving model (D26), on
      the fresh `m4g-` schedule (D5: one fresh problem per trial, alternating the
      author's two logic grammars, SHARED across models). Resume-aware, append-only.
  grid — lossy / lossy_padded / source_first × g ∈ {0.1, 0.3}, N = 60 FLAT (D26: no
      escalation ladder — nothing gates on the wide-CI floor, so the flexible-N degree
      of freedom stays closed by fixing N). Directed corrections only (D2). Every note
      passes the per-trial source gate in both directions before its trial spends a
      token (runner.verify_note_gate, inside run_session2).
  checkpoint — the scheduled N=20 interim look, $0: a seeded ≥3-trial hand-read
      sample per cell (the M0 scoring lesson bites hardest on a brand-new readout —
      bug-catching first, futility second) plus the light futility note (the gap
      trend, descriptive; nothing stops or clears here).
  judge — the D25 gates, $0, a pure function of the logged rows. Judging is ONCE, at
      N=60.
  figure — reclaim vs g per model with Wilson bars + the wall taxonomy stack
      (docs/figs/m4-logic-wall.png).

Sampling is D10's, imported from m0.py — never redefined. The roster is D13's frozen
trio, imported from m1.py; the D24 pilot may sit models out but never adds any.

Run (paid steps gated on `uv run pytest` green, per the brief):
    uv run m4.py pilot [n] [model]     # D24: ~20 session-1 takes + the wall read
    uv run m4.py bank [target] [model] # session-1 bank to `target` taken (default 60)
    uv run m4.py grid [n] [model]      # extend all six cells to n (default 20)
    uv run m4.py checkpoint [model]    # $0: the hand-read sample + the futility note
    uv run m4.py judge [model]         # $0: D25 gates, taxonomy, verdicts
    uv run m4.py figure                # $0: docs/figs/m4-logic-wall.png
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict, replace
from pathlib import Path

from grader import ABST, INHERIT, LOGIC_BUCKETS, NOVEL, RECOV, classify_logic, \
    is_hedged, parse_answer_word, took_logic
from m0 import MAX_TOKENS, PILOT_N, PROBE_G, SEED, TEMPERATURE, d8_verdict, \
    openrouter_factory
from m1 import CEILING, ROSTER, _append_jsonl, _cell_key, _cells_from_rows, \
    _pick_models, _print_cost, _read_jsonl, _write_trajectory
from notes import memory_note
from problems import Problem
from problems_gen import gen_assign, gen_logic, validate_assign, validate_logic
from runner import build_trajectory, run_session2, take_probe
from stats import excludes_zero, newcombe_diff, wilson

# ── the settled constants (D23–D26; sampling/roster imported, never redefined) ───────

GRID_G: tuple[float, ...] = (0.1, 0.3)   # the wall region (D2's knob, low end)
GRID_POLICIES: tuple[str, ...] = ("lossy", "lossy_padded", "source_first")
N_BANK = 60          # D26: N=60 flat — bought for the descriptive floor
N_CHECKPOINT = 20    # the scheduled interim look: hand-read + futility note only
                     # (no N_MAX: D26 pre-commits NO escalation ladder)

# D24's tier IS D8's (the 14/10-at-20 lines, held as fractions) — imported
pilot_tier = d8_verdict

# ── the PAPER anchor (rider a): arXiv v2 Table 6, llama·logic wall cells ─────────────
# Two-pass verbatim extraction, 2026-07-08 (evidence/m4/paper-extraction-logic.md).
# The README artifact prints lossy 0.25/0.12, padded 0.25/0.04, sf 0.67/0.67 for the
# same cells — a divergence on every cell (the M3 arithmetic-row precedent, larger
# here; the v2 parser fix is the likely mover). The PAPER values are the pre-registered
# comparison target; no gate consumes them (direction + structure only, KICKOFF).
PAPER: dict = {
    "llama": {
        "lossy":        {0.3: 0.16, 0.1: 0.05},
        "lossy_padded": {0.3: 0.18, 0.1: 0.09},
        "source_first": {0.3: 0.76, 0.1: 0.79},
    },
}
PAPER_SOURCE = ("arXiv 2606.25449v2 Table 6 — 'Constraint logic: the same three "
                "policies, two models. Directed RR (95% CI) vs. memory integrity g "
                "(llama n=96; grok n=24).' Two-pass verbatim extraction 2026-07-08; "
                "README-vs-paper variance footnoted in "
                "evidence/m4/paper-extraction-logic.md")


# ── the D25 gates as pure functions (test_m4 pins the boundary arithmetic) ───────────

def gap_gate(k_base: int, n_base: int, k_sf: int, n_sf: int) -> dict:
    """The gap instrument for both claims: Newcombe 95% on (source_first − base),
    where base is lossy (claim 1) or lossy_padded (claim 2). The gate is `positive`:
    the whole interval above zero."""
    d, lo, hi = newcombe_diff(k_base, n_base, k_sf, n_sf)
    return {"d": d, "lo": lo, "hi": hi, "positive": lo > 0.0}


def claim_model_verdict(gap_positive_by_g: dict) -> str:
    """A model clears a claim only if its gap excludes zero at BOTH wall g; one g
    only is PARTIAL (structure — where the softness lives — not a pass)."""
    passes = list(gap_positive_by_g.values())
    if all(passes):
        return "cleared"
    return "partial" if any(passes) else "not_cleared"


def shape_reads(k_lossy: int, n_lossy: int, k_sf: int, n_sf: int) -> dict:
    """One wall g's shape read on the anchored model, mechanized with v1's
    pre-committed smallness scale mirrored at both ends (no new constants):
      floor_soft    — the lossy floor is NOT consistent-with-~0 (Wilson upper bound
                      above CEILING; clearing v1's ceiling here would mean a HARDER
                      wall than the paper finds on logic — a divergence);
      sf_below_one  — the fix is NOT consistent-with-~1 (Wilson lower bound under
                      1 − CEILING; reaching ~1 is the arithmetic regime);
      gap_positive  — the claim-1 gate itself."""
    return {"floor_soft": wilson(k_lossy, n_lossy)[1] > CEILING,
            "sf_below_one": wilson(k_sf, n_sf)[0] < 1.0 - CEILING,
            "gap_positive": gap_gate(k_lossy, n_lossy, k_sf, n_sf)["positive"]}


def anchor_shape_matches(reads_by_g: dict) -> bool:
    """The paper's soft-wall shape holds only if all three reads hold at BOTH g."""
    return all(r["floor_soft"] and r["sf_below_one"] and r["gap_positive"]
               for r in reads_by_g.values())


# the pre-committed verdict vocabulary (D25)
REPRODUCED, PARTIAL, NULL, DISCREPANT = "REPRODUCED", "PARTIAL", "NULL", "DISCREPANT"


def m4_claim_verdict(model_verdicts: dict, anchor_shape: bool | None = None,
                     crosscheck: str | None = None) -> str:
    """The D25 mapping, fixed before any data: REPRODUCED needs the ≥2-of-3 bar
    (KICKOFF) and — for claim 1, where a shape read applies — the anchored model's
    soft-wall shape; NULL is the pre-registered no-gap-anywhere verdict (the fix does
    NOT generalize — reportable, not a failure); everything between is PARTIAL,
    reported as structure. DISCREPANT only via a scope-B cross-check judgement."""
    if crosscheck == "discrepant":
        return DISCREPANT
    vs = list(model_verdicts.values())
    if sum(v == "cleared" for v in vs) >= 2 and anchor_shape is not False:
        return REPRODUCED
    if all(v == "not_cleared" for v in vs):
        return NULL
    return PARTIAL


EQUIVALENCE_CAVEAT = (
    "padded ≈ lossy is reported descriptively, never gated: δ=0.10 equivalence is "
    "unpowerable at hobby N on a mid-range rate (Newcombe ±0.15 at N=60 on rates "
    "≈0.25; ~N≥150/arm would be needed) — pre-registered in docs/M4-BRIEF.md (D25).")


def equivalence_report(k_lossy: int, n_lossy: int, k_pad: int, n_pad: int) -> dict:
    """The claim-2 equivalence half, DESCRIPTIVE only: both rates, the Newcombe
    interval on (padded − lossy), the plain overlap statement, the caveat. There is
    deliberately no verdict key."""
    d, lo, hi = newcombe_diff(k_lossy, n_lossy, k_pad, n_pad)
    return {"d": d, "lo": lo, "hi": hi,
            "lossy": (k_lossy, n_lossy), "padded": (k_pad, n_pad),
            "overlaps_zero": not excludes_zero(lo, hi),
            "caveat": EQUIVALENCE_CAVEAT}


def taxonomy_summary(rows: list[dict]) -> dict:
    """The four-way readout over graded rows ({'bucket', 'k_options'}), with the
    chance floor: a pure guesser on a closed set of k options scores ~1/k, so the
    mean 1/k is stated wherever a rate is read (a lossy recov near the floor is
    guessing-compatible, not re-derivation)."""
    counts = {b: 0 for b in LOGIC_BUCKETS}
    for r in rows:
        counts[r["bucket"]] += 1
    n = len(rows)
    floor = sum(1.0 / r["k_options"] for r in rows) / n if n else None
    return {"n": n, "counts": counts, "chance_floor": floor}


# ── the m4 problem schedules (D5: fresh per trial, both grammars, shared) ────────────

def _schedule_problem(namespace: str, seed: int, trial: int, pid: str) -> Problem:
    """Trial i's freshly minted logic problem: the author's own generation grammar
    seeded per (namespace, seed, trial), alternating the two logic families (even =
    ordering, odd = assignment) so the trial diet mixes both, exactly as the author's
    own 32-problem pool does. Validated before return; a bad instance raises."""
    gen_seed = random.Random(f"{namespace}-{seed}-trial-{trial}").randrange(2 ** 31)
    if trial % 2 == 0:
        p = replace(gen_logic(1, seed=gen_seed)[0], pid=pid)
        validate_logic([p])
    else:
        p = replace(gen_assign(1, seed=gen_seed)[0], pid=pid)
        validate_assign([p])
    return p


def bank_problem(seed: int, trial: int) -> Problem:
    """Trial i's problem on the M4 bank schedule (`m4g…` pids, disjoint from the
    pilot's and from every v1 namespace)."""
    return _schedule_problem("m4", seed, trial, f"m4g{seed}-{trial:02d}")


def pilot_problem(seed: int, trial: int) -> Problem:
    """Trial i's problem on the D24 pilot schedule (`m4p…` pids — pilot problems are
    never reused by the bank, mirroring the M0/M1 namespace split)."""
    return _schedule_problem("m4p", seed, trial, f"m4p{seed}-{trial:02d}")


def _load_problem(rec: dict) -> Problem:
    """A Problem back from its JSONL dict (options re-tupled after the JSON round
    trip)."""
    return Problem(**{**rec, "options": tuple(rec.get("options") or ())})


# ── the D24 pilot ─────────────────────────────────────────────────────────────────────

def run_pilot(llm_for, n: int = PILOT_N, seed: int = SEED, runs_root="runs",
              models: dict[str, str] = ROSTER, wall_g: float = PROBE_G) -> dict[str, dict]:
    """The logic drift-take pilot, per model: n session-1 trajectories on the `m4p-`
    schedule, take = took_logic on the (never-carried) take probe; each TAKEN trial
    additionally gets one lossy@wall_g directed session-2 call, taxonomy-classified —
    the disposition read that doubles as the claim-3-on-logic powerability probe.
    Resume-aware and append-only, like every runner here."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        pilot_dir = root / f"m4-pilot-{key}"
        pilot_dir.mkdir(parents=True, exist_ok=True)
        results_path = pilot_dir / "results.jsonl"
        rows = _read_jsonl(results_path)
        for trial in range(len(rows), n):
            problem = pilot_problem(seed, trial)
            llm = llm_for(slug, problem)
            cost0 = getattr(llm, "cost", 0.0)
            trajectory = build_trajectory(llm, problem)
            reply = take_probe(llm, trajectory, problem)   # D11: never carried
            take = took_logic(reply, problem)
            wall_reply = wall_bucket = None
            if take:
                wall_reply = run_session2(llm_for(slug, problem), problem,
                                          "lossy", wall_g, arm="directed")
                wall_bucket = classify_logic(wall_reply, problem)
            _write_trajectory(pilot_dir / f"trial-{trial:02d}.jsonl", trajectory)
            row = {"trial": trial, "pid": problem.pid, "model": slug,
                   "temperature": getattr(llm, "temperature", None),
                   "took": bool(take),
                   "parsed": parse_answer_word(reply, problem.options),
                   "take_reply": reply, "wall_g": wall_g if take else None,
                   "wall_bucket": wall_bucket, "wall_reply": wall_reply,
                   "k_options": len(problem.options),
                   "cost": round(getattr(llm, "cost", 0.0) - cost0, 8),
                   "problem": asdict(problem)}
            rows.append(row)
            _append_jsonl(results_path, row)
            print(f"  [{key}] pilot trial {trial:02d} {problem.pid}: took={bool(take)}"
                  f"{f' wall={wall_bucket}' if take else ''}", flush=True)
        takes = sum(r["took"] for r in rows)
        taxonomy = taxonomy_summary([{"bucket": r["wall_bucket"],
                                      "k_options": r["k_options"]}
                                     for r in rows if r["took"] and r["wall_bucket"]])
        out[key] = {"label": f"m4-pilot-{key}", "slug": slug, "n": len(rows),
                    "takes": takes, "tier": pilot_tier(takes, len(rows)),
                    "taxonomy": taxonomy}
        print(f"  [{key}] pilot: {takes}/{len(rows)} took -> {out[key]['tier'].upper()}"
              f" | wall taxonomy {taxonomy['counts']}", flush=True)
    return out


# ── the trajectory bank (mirrors m1.run_bank on the logic readout) ───────────────────

def run_bank(llm_for, target: int = N_BANK, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = ROSTER) -> dict[str, dict]:
    """Extend each model's logic bank until `target` trajectories TOOK. Resume-aware
    and append-only; a take-starved model stops at a bounded budget and reports
    `short` honestly (its D24 tier decides its fate, not the bank loop)."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        bank_dir = root / f"m4-bank-{key}"
        bank_dir.mkdir(parents=True, exist_ok=True)
        results_path = bank_dir / "results.jsonl"
        rows = _read_jsonl(results_path)
        if rows and not rows[0]["pid"].startswith(f"m4g{seed}-"):
            raise ValueError(f"{results_path} carries pid {rows[0]['pid']!r} — a "
                             f"different seed than {seed}; refusing to mix schedules")
        takes = sum(r["took"] for r in rows)
        next_trial = len(rows)
        budget = 2 * max(0, target - takes) + 8
        while takes < target and budget > 0:
            problem = bank_problem(seed, next_trial)
            llm = llm_for(slug, problem)
            calls0 = getattr(llm, "calls", 0)
            cost0 = getattr(llm, "cost", 0.0)
            trajectory = build_trajectory(llm, problem)
            reply = take_probe(llm, trajectory, problem)   # D11: never carried
            take = took_logic(reply, problem)
            takes += take
            _write_trajectory(bank_dir / f"trial-{next_trial:02d}.jsonl", trajectory)
            row = {"trial": next_trial, "pid": problem.pid, "model": slug,
                   "temperature": getattr(llm, "temperature", None),
                   "took": bool(take),
                   "parsed": parse_answer_word(reply, problem.options),
                   "take_reply": reply,
                   "calls": getattr(llm, "calls", 0) - calls0,
                   "cost": round(getattr(llm, "cost", 0.0) - cost0, 8),
                   "problem": asdict(problem)}
            rows.append(row)
            _append_jsonl(results_path, row)
            print(f"  [{key}] bank trial {next_trial:02d} {problem.pid}: "
                  f"took={bool(take)} ({takes}/{target})", flush=True)
            next_trial += 1
            budget -= 1
        out[key] = {"label": f"m4-bank-{key}", "slug": slug, "trials": len(rows),
                    "takes": takes, "target": target, "short": takes < target}
        print(f"  [{key}] bank: {takes}/{target} taken in {len(rows)} trials"
              f"{' — SHORT' if out[key]['short'] else ''}", flush=True)
    return out


def load_bank(runs_root, key: str, seed: int = SEED) -> list[tuple[int, Problem]]:
    """The taken bank entries, in schedule order — what the grid consumes."""
    path = Path(runs_root) / f"m4-bank-{key}" / "results.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no bank at {path} — run `uv run m4.py bank` first")
    rows = _read_jsonl(path)
    if not rows:
        raise ValueError(f"{path} is empty — re-run the bank")
    if not rows[0]["pid"].startswith(f"m4g{seed}-"):
        raise ValueError(f"m4-bank-{key} rows carry pid {rows[0]['pid']!r} — a "
                         f"different seed than {seed}; the grid must consume the "
                         f"SAME schedule")
    return [(r["trial"], _load_problem(r["problem"])) for r in rows if r["took"]]


# ── the grid runner (N=60 flat: every cell the same size, D26) ───────────────────────

def run_grid(llm_for, n: int = N_CHECKPOINT, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = ROSTER, gs: tuple[float, ...] = GRID_G,
             policies: tuple[str, ...] = GRID_POLICIES) -> dict[str, dict]:
    """Extend every (policy, g) cell to n trials over the bank, in bank order,
    appending only the missing trials. No per-policy caps and no escalation: D26
    fixed N flat, so every cell walks the same schedule to the same size."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        bank = load_bank(root, key, seed)
        grid_dir = root / f"m4-grid-{key}"
        grid_dir.mkdir(parents=True, exist_ok=True)
        results_path = grid_dir / "results.jsonl"
        rows = _read_jsonl(results_path)
        done: dict[str, int] = {}
        for r in rows:
            ck = _cell_key(r["policy"], r["g"])
            done[ck] = done.get(ck, 0) + 1
        cells: dict[str, dict] = {}
        short = False
        for policy in policies:
            for g in gs:
                ck = _cell_key(policy, g)
                have = done.get(ck, 0)
                want = min(n, len(bank))
                if n > len(bank):
                    short = True
                for t, problem in bank[have:want]:
                    llm = llm_for(slug, problem)
                    cost0 = getattr(llm, "cost", 0.0)
                    reply = run_session2(llm, problem, policy, g, arm="directed")
                    bucket = classify_logic(reply, problem)
                    _append_jsonl(results_path, {
                        "bank_trial": t, "pid": problem.pid, "policy": policy, "g": g,
                        "note": memory_note(problem, g, policy), "reply": reply,
                        "parsed": parse_answer_word(reply, problem.options),
                        "hedged": is_hedged(reply), "bucket": bucket,
                        "reclaimed": bucket == RECOV,
                        "k_options": len(problem.options), "model": slug,
                        "temperature": getattr(llm, "temperature", None),
                        "cost": round(getattr(llm, "cost", 0.0) - cost0, 8)})
                    print(f"  [{key}] {ck} trial {t:02d} {problem.pid}: {bucket}",
                          flush=True)
                cells[ck] = {"ran": max(0, want - have)}
        rows = _read_jsonl(results_path)
        for ck, cell in cells.items():
            cell_rows = [r for r in rows if _cell_key(r["policy"], r["g"]) == ck]
            cell["n"] = len(cell_rows)
            cell["k"] = sum(r["reclaimed"] for r in cell_rows)
        out[key] = {"label": f"m4-grid-{key}", "slug": slug, "cells": cells,
                    "short": short}
        summary = "  ".join(f"{ck} {c['k']}/{c['n']}" for ck, c in cells.items())
        print(f"  [{key}] grid: {summary}{' — SHORT BANK' if short else ''}", flush=True)
    return out


# ── the checkpoint and the judge — pure readers of the JSONL ─────────────────────────

def checkpoint(runs_root, models: dict[str, str] = ROSTER, sample_k: int = 3,
               rng_seed: int = 0) -> dict[str, dict]:
    """The scheduled N=20 interim look, $0. Its FIRST job on a brand-new readout is
    bug-catching: a seeded ≥3-trial hand-read sample per cell (eyes on raw replies vs
    the parsed bucket). The futility half is a LIGHT NOTE (D26): the current gap trend,
    descriptive — nothing stops, clears, or escalates here; judging is once, at N=60."""
    out: dict[str, dict] = {}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m4-grid-{key}" / "results.jsonl")
        by_cell = _cells_from_rows(rows)
        cells: dict[str, dict] = {}
        for ck, cell_rows in by_cell.items():
            k = sum(r["reclaimed"] for r in cell_rows)
            rng = random.Random(f"{rng_seed}-{key}-{ck}")
            sample = rng.sample(cell_rows, min(sample_k, len(cell_rows)))
            cells[ck] = {"k": k, "n": len(cell_rows), "sample": sample,
                         "taxonomy": taxonomy_summary(cell_rows)}
        gap_trend: dict[str, dict] = {}
        for g in GRID_G:
            lc = cells.get(_cell_key("lossy", g))
            sc = cells.get(_cell_key("source_first", g))
            if lc and sc:
                gap_trend[f"{g:g}"] = gap_gate(lc["k"], lc["n"], sc["k"], sc["n"])
        out[key] = {"cells": cells, "gap_trend": gap_trend}
    return out


def judge(runs_root, models: dict[str, str] = ROSTER, anchor: str = "llama") -> dict:
    """The D25 gates, $0, a pure function of the logged rows: per-cell Wilson +
    taxonomy + chance floor, the claim-1 gap and claim-2 separation per g, the
    equivalence report (descriptive), the anchored shape read, and the pre-committed
    verdict mapping. The anchor is llama — the one model with a published logic
    comparison target (PAPER); its paper values ride along descriptively."""
    result: dict = {"models": {}, "anchor_shape": {"model": anchor, "reads": None,
                                                   "matches": None}}
    claim1_by_model: dict[str, str] = {}
    claim2_by_model: dict[str, str] = {}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m4-grid-{key}" / "results.jsonl")
        by_cell = _cells_from_rows(rows)
        cells: dict[str, dict] = {}
        for ck, cell_rows in by_cell.items():
            k, n = sum(r["reclaimed"] for r in cell_rows), len(cell_rows)
            lo, hi = wilson(k, n)
            tax = taxonomy_summary(cell_rows)
            policy, g = ck.split("@")
            cells[ck] = {"k": k, "n": n, "rate": k / n if n else 0.0,
                         "wilson_lo": lo, "wilson_hi": hi,
                         "taxonomy": tax["counts"],
                         "chance_floor": tax["chance_floor"],
                         "paper": PAPER.get(key, {}).get(policy, {}).get(float(g))}
        gaps1: dict[str, dict] = {}
        gaps2: dict[str, dict] = {}
        equivalence: dict[str, dict] = {}
        for g in GRID_G:
            lc = cells.get(_cell_key("lossy", g))
            pc = cells.get(_cell_key("lossy_padded", g))
            sc = cells.get(_cell_key("source_first", g))
            gk = f"{g:g}"
            if lc and sc:
                gaps1[gk] = gap_gate(lc["k"], lc["n"], sc["k"], sc["n"])
            if pc and sc:
                gaps2[gk] = gap_gate(pc["k"], pc["n"], sc["k"], sc["n"])
            if lc and pc:
                equivalence[gk] = equivalence_report(lc["k"], lc["n"], pc["k"], pc["n"])
        c1 = claim_model_verdict({g: gp["positive"] for g, gp in gaps1.items()}) \
            if gaps1 else None
        c2 = claim_model_verdict({g: gp["positive"] for g, gp in gaps2.items()}) \
            if gaps2 else None
        if c1:
            claim1_by_model[key] = c1
        if c2:
            claim2_by_model[key] = c2
        result["models"][key] = {"cells": cells, "gaps_claim1": gaps1,
                                 "gaps_claim2": gaps2, "equivalence": equivalence,
                                 "claim1_verdict": c1, "claim2_verdict": c2}
        if key == anchor and gaps1:
            reads = {}
            for g in GRID_G:
                lc = cells.get(_cell_key("lossy", g))
                sc = cells.get(_cell_key("source_first", g))
                if lc and sc:
                    reads[f"{g:g}"] = shape_reads(lc["k"], lc["n"], sc["k"], sc["n"])
            result["anchor_shape"] = {"model": anchor, "reads": reads,
                                      "matches": anchor_shape_matches(reads)}
    result["claim1"] = m4_claim_verdict(
        claim1_by_model, anchor_shape=result["anchor_shape"]["matches"]) \
        if claim1_by_model else None
    result["claim2"] = m4_claim_verdict(claim2_by_model, anchor_shape=None) \
        if claim2_by_model else None
    return result


# ── the soft-wall figure ─────────────────────────────────────────────────────────────

FIGURE_PATH = Path("docs/figs/m4-logic-wall.png")
_BUCKET_COLORS = {RECOV: "#2471a3", INHERIT: "#c0392b", NOVEL: "#e67e22",
                  ABST: "#95a5a6"}


def make_figure(judged: dict, path=FIGURE_PATH) -> None:
    """Two rows per model: reclaim (recov) rate vs g with Wilson bars for the three
    policies, and the wall taxonomy stack (recov/inherit/novel/abst fractions per
    policy × g) — the soft floor made visible."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = judged["models"]
    ncols = max(1, len(models))
    fig, axes = plt.subplots(2, ncols, figsize=(5.2 * ncols, 8.0), squeeze=False)
    for col, (key, m) in enumerate(models.items()):
        ax = axes[0][col]
        for policy, color, marker in (("lossy", "#c0392b", "o"),
                                      ("lossy_padded", "#e67e22", "^"),
                                      ("source_first", "#2471a3", "s")):
            xs, ys, lo_err, hi_err, ns = [], [], [], [], []
            for g in GRID_G:
                cell = m["cells"].get(_cell_key(policy, g))
                if cell is None:
                    continue
                xs.append(g)
                ys.append(cell["rate"])
                lo_err.append(cell["rate"] - cell["wilson_lo"])
                hi_err.append(cell["wilson_hi"] - cell["rate"])
                ns.append(cell["n"])
            ax.errorbar(xs, ys, yerr=[lo_err, hi_err], color=color, marker=marker,
                        capsize=4, label=policy)
            for x, y, n in zip(xs, ys, ns):
                ax.annotate(f"n={n}", (x, y), textcoords="offset points",
                            xytext=(6, 6), fontsize=8, color=color)
        ax.set_xticks(GRID_G)
        ax.set_xlim(0.0, 0.42)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("note integrity g")
        ax.set_title(key)
        ax.grid(alpha=0.25)
        if col == 0:
            ax.set_ylabel("reclaim (recov) rate, directed")
            ax.legend(loc="center right", fontsize=8)
        # the taxonomy stack at the wall
        axb = axes[1][col]
        labels, bottoms = [], []
        for policy in GRID_POLICIES:
            for g in GRID_G:
                cell = m["cells"].get(_cell_key(policy, g))
                if cell is None:
                    continue
                labels.append((f"{policy}\n@{g:g}", cell))
        xs = range(len(labels))
        base = [0.0] * len(labels)
        for bucket in LOGIC_BUCKETS:
            fracs = [c["taxonomy"].get(bucket, 0) / c["n"] if c["n"] else 0.0
                     for _, c in labels]
            axb.bar(xs, fracs, bottom=base, color=_BUCKET_COLORS[bucket],
                    label=bucket, width=0.7)
            base = [b + f for b, f in zip(base, fracs)]
        axb.set_xticks(list(xs))
        axb.set_xticklabels([lbl for lbl, _ in labels], fontsize=7)
        axb.set_ylim(0, 1.0)
        axb.grid(alpha=0.25, axis="y")
        if col == 0:
            axb.set_ylabel("fraction of trials")
            axb.legend(loc="upper right", fontsize=8)
    fig.suptitle("M4 — the soft wall: logic reclaim vs integrity, and the wall "
                 "taxonomy (Wilson 95%)")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ── CLI ──────────────────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    cmds = ("pilot", "bank", "grid", "checkpoint", "judge", "figure")
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "pilot":
        n = int(argv[2]) if len(argv) > 2 else PILOT_N
        models = _pick_models(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M4 pilot (D24): {n} session-1 logic trials/model + the lossy@{PROBE_G} "
              f"wall read, temperature {TEMPERATURE}\n")
        out = run_pilot(llm_for, n=n, models=models)
        print("\nD24 tiers: green >=70% take — proceed; amber 50–70% — audit the "
              "recipe once, inflate generation by 1/t-hat; trigger <50% — the model "
              "sits out M4's grid.")
        for key, r in out.items():
            print(f"  [{key}] {r['takes']}/{r['n']} -> {r['tier'].upper()} | wall "
                  f"taxonomy {r['taxonomy']['counts']} (chance floor "
                  f"~{r['taxonomy']['chance_floor'] or 0:.2f})")
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "bank":
        target = int(argv[2]) if len(argv) > 2 else N_BANK
        models = _pick_models(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M4 bank: to {target} taken/model, depth 8, temperature {TEMPERATURE}\n")
        run_bank(llm_for, target=target, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "grid":
        n = int(argv[2]) if len(argv) > 2 else N_CHECKPOINT
        models = _pick_models(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M4 grid: all six cells to n={n} flat (D26), directed only, "
              f"temperature {TEMPERATURE}\n")
        run_grid(llm_for, n=n, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "checkpoint":
        models = _pick_models(argv[2] if len(argv) > 2 else None)
        out = checkpoint("runs", models)
        for key, m in out.items():
            print(f"\n[{key}] checkpoint — hand-read sample first (new readout: "
                  f"bug-catch before futility), then the light futility note")
            for ck, cell in sorted(m["cells"].items()):
                print(f"  {ck}: {cell['k']}/{cell['n']} recov | taxonomy "
                      f"{cell['taxonomy']['counts']}")
            for g, gap in m["gap_trend"].items():
                print(f"  gap trend (sf - lossy) @ g={g}: {gap['d']:+.0%} "
                      f"[{gap['lo']:+.1%}, {gap['hi']:+.1%}] (descriptive — nothing "
                      f"gates at N=20)")
            for ck, cell in sorted(m["cells"].items()):
                print(f"\n  ── hand-read sample for {ck} "
                      f"({len(cell['sample'])} trials) " + "─" * 30)
                for r in cell["sample"]:
                    print(f"\n  trial {r['bank_trial']} {r['pid']} -> {r['bucket']}"
                          f" (parsed={r.get('parsed')}, hedged={r.get('hedged')})")
                    print(f"  NOTE : {r.get('note')}")
                    print(f"  REPLY: {r.get('reply')}")
        return 0

    if cmd == "judge":
        models = _pick_models(argv[2] if len(argv) > 2 else None)
        out = judge("runs", models)
        print("M4 judge — D25: claim 1 gates the GAP (sf − lossy > 0, both g), "
              "claim 2 gates SEPARATION (sf − padded > 0, both g); the soft floor "
              "and the equivalence are reported, never gated\n")
        for key, m in out["models"].items():
            print(f"[{key}]")
            for ck, cell in sorted(m["cells"].items()):
                paper = f"  paper {cell['paper']:.2f}" if cell.get("paper") else ""
                print(f"  {ck:<22} {cell['k']:>3}/{cell['n']:<3} "
                      f"Wilson [{cell['wilson_lo']:.1%}, {cell['wilson_hi']:.1%}] "
                      f"taxonomy {cell['taxonomy']} floor ~{cell['chance_floor']:.2f}"
                      f"{paper}")
            for g, gap in m["gaps_claim1"].items():
                print(f"  claim-1 gap (sf - lossy) @ g={g}: {gap['d']:+.0%} "
                      f"[{gap['lo']:+.1%}, {gap['hi']:+.1%}]"
                      f" {'POSITIVE' if gap['positive'] else 'not positive'}")
            for g, gap in m["gaps_claim2"].items():
                print(f"  claim-2 sep (sf - padded) @ g={g}: {gap['d']:+.0%} "
                      f"[{gap['lo']:+.1%}, {gap['hi']:+.1%}]"
                      f" {'POSITIVE' if gap['positive'] else 'not positive'}")
            for g, eq in m["equivalence"].items():
                tag = "overlap" if eq["overlaps_zero"] else "SEPARATED"
                print(f"  equivalence (padded - lossy) @ g={g}: {eq['d']:+.0%} "
                      f"[{eq['lo']:+.1%}, {eq['hi']:+.1%}] — {tag} (descriptive)")
            print(f"  claim-1 verdict: {m['claim1_verdict']}   claim-2 verdict: "
                  f"{m['claim2_verdict']}\n")
        sh = out["anchor_shape"]
        if sh["reads"]:
            print(f"anchor shape ({sh['model']}): "
                  + "  ".join(f"g={g}: floor_soft={r['floor_soft']} "
                              f"sf_below_one={r['sf_below_one']} "
                              f"gap={r['gap_positive']}" for g, r in sh["reads"].items())
                  + f" -> matches={sh['matches']}")
        print(f"\nM4 claim-1 verdict: {out['claim1']}")
        print(f"M4 claim-2 verdict: {out['claim2']}")
        print(f"\n({EQUIVALENCE_CAVEAT})")
        return 0

    # figure
    out = judge("runs", dict(ROSTER))
    make_figure(out, FIGURE_PATH)
    print(f"wrote {FIGURE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
