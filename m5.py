"""m5.py — the source-size boundary arm (bank → grid → checkpoint → judge → figure),
the paper's own design (D28-B), with D29's cliff gate + verdict mapping pre-committed.

M5 is the falsification stage. v1 measured the source_first FIX working (~1.00 reclaim vs
~0.00 lossy at the wall); M5 asks where the fix FAILS. The fix keeps the recomputable
source and drops the re-derivable conclusion — but only if the source fits the note budget.
FIX THE CHARACTER BUDGET B AND GROW THE SOURCE SIZE N (line items): as N outgrows B the
source_first note keeps only k<N whole items, and an exact sum needs all N, so its reclaim
advantage cliffs to the lossy floor. Run TWO budgets — the crossover (largest N where
source_first still reclaims) moves with B, which is how the paper disentangles
budget-starvation from problem difficulty: "the cliff tracks the budget, not problem size."

This is the author's released `bench_sizesweep.py` design, rebuilt independently (D6:
reference, re-type, never import). The anchor is CONCRETE, not thin (the M5 brief's
assumption was corrected by the extraction, evidence/m5/paper-extraction-boundary.md):
crossover N≈5 at B=300, N≈14 at B=600; "cliffs to 0.00 the instant one item is dropped";
past the boundary source_first does not abstain — it SILENTLY MIS-SUMS the partial source to
the stale value (EMIT_ATTRACTOR, worse-than-empty). The comparison is direction + structure,
never point-matched; there is no oracle overlap cell here, so no DISCREPANT verdict.

D29's gate (signed 2026-07-09; D28 reopened to the paper design 2026-07-09), pure functions
below, pinned by test_m5:
  ceiling intact — source_first at the SMALLEST N (source fits) reclaims: Wilson-95 lower
      bound clears CLIFF_CEIL = 0.80 (no working fix ⇒ nothing to break).
  the drop      — per budget, Newcombe-95 on (RR@min-N − RR@max-N) EXCLUDES ZERO
      (source_first falls as the source is grown past the budget).
  monotone      — reclaim is non-increasing as N grows, within noise.
  tracks budget — crossover(large budget) > crossover(small budget): the cliff location
      moves with B, not with N — the paper's central structural claim (needs ≥2 budgets).
  mechanism     — pooled across budgets, source_first reclaim split by whether the FULL
      source fit (k==N) vs partial (k<N): full ≫ partial (the k<N information wall), the
      Newcombe excluding zero.
  confound-clean — the N=20 checkpoint hand-read confirms genuine recompute-failure, not a
      truncation/gate bug (a flag passed to the verdict).
  verdict mapping (REPRODUCED / PARTIAL / NULL — no DISCREPANT):
      REPRODUCED — ceiling + drop + monotone at BOTH budgets AND tracks-budget AND the
          mechanism split AND confound-clean: the fix is bounded and the boundary is the
          source-to-budget ratio, exactly as the paper finds.
      NULL       — no drop at either budget AND source_first stays robust at max N (Wilson
          lower bound ≥ ROBUST_FLOOR = 0.50): the fix survived source growth in our range —
          reportable, slightly-better news, not a failure.
      PARTIAL    — everything between (a drop at one budget only, no crossover movement, a
          confound, no working fix at small N). Reported as structure.
  the crossover per budget, the lossy_padded floor, and the silent-mis-sum outcome split
      are REPORTED with Wilson CIs, never gated.

Arithmetic is the clean family: an OPEN-number answer, no closed-set guess floor. The model
is deepseek (D27): terse (no token-cap confound), reclaims source_first ~1.00 at small N
(headroom), answers rather than abstains. lossy_padded is the paper's budget-matched floor
(same length as source_first, so the cliff can't be "less text"). One N-bank per source size
feeds both budgets and both policies (D5 pairing: the budget/policy is a note-write-time
knob over the same taken trajectory).

Sampling is D10's, imported from m0.py; the roster slug is D13's, imported from m1.py. M5
changes nothing frozen and re-judges no prior cell.

Run (paid steps gated on `uv run pytest` green + Kyle's go, per the brief):
    uv run m5.py bank [target] [model]   # session-1 banks, one per source size N (default 40)
    uv run m5.py grid [n] [model]        # extend all N×budget×policy cells to n (default 20)
    uv run m5.py checkpoint [model]      # $0: hand-read sample + the cliff trend (nothing gates)
    uv run m5.py judge [model]           # $0: D29 cliff gate, crossover, mechanism, verdict
    uv run m5.py figure [model]          # $0: docs/figs/m5-boundary.png
"""
from __future__ import annotations

import random
import sys
from dataclasses import asdict
from pathlib import Path

from grader import OUTCOMES, RECLAIMED, grade, parse_answer, took
from m0 import SEED, TEMPERATURE, openrouter_factory
from m1 import ROSTER, _append_jsonl, _print_cost, _read_jsonl, _write_trajectory
from notes import build_sized_note, item_clauses, retained_fraction
from problems import Problem, generate_sized
from runner import build_trajectory, run_session2_budget, take_probe
from stats import newcombe_diff, wilson

# ── the settled constants (D27–D30; sampling/roster imported, never redefined) ───────

NS: tuple[int, ...] = (2, 4, 6, 8, 12, 16, 24)   # D28-B/D30: the source-size grid,
                                                 # bracketing both crossovers (paper ≈5, ≈14)
BUDGETS: tuple[int, ...] = (300, 600)            # the paper's two char budgets (D28-B)
GRID_POLICIES: tuple[str, ...] = ("source_first", "lossy_padded")   # the paper's two arms
N_BANK = 40          # D30: taken trajectories per source size N (confirm at the paid gate)
N_TRIALS = 40        # D30: trials per cell (judge once at this N)
N_CHECKPOINT = 20    # the scheduled interim look (D30: no escalation ladder)

# D27: one model. deepseek — terse, reclaims source_first ~1.00 at small N, answers.
M5_MODEL = "deepseek"
M5_MODELS: dict[str, str] = {M5_MODEL: ROSTER[M5_MODEL]}

# D29's pre-committed constants (test_m5 pins the boundary arithmetic)
CLIFF_CEIL = 0.80      # "ceiling intact": source_first at the smallest N, Wilson-95 lower bound
ROBUST_FLOOR = 0.50    # NULL: source_first at the largest N still holds above this
CROSSOVER_LEVEL = 0.5  # the boundary of the law: source_first still reclaims above this

REPRODUCED, PARTIAL, NULL = "REPRODUCED", "PARTIAL", "NULL"   # no DISCREPANT (no oracle cell)


# ── the D29 gate as pure functions ───────────────────────────────────────────────────

def ceiling_intact(k_small_n: int, n_small_n: int) -> bool:
    """Is there a working fix to break? source_first at the SMALLEST N (the source fits)
    reclaims — its Wilson-95 lower bound clears CLIFF_CEIL."""
    return wilson(k_small_n, n_small_n)[0] >= CLIFF_CEIL


def real_drop(k_small_n: int, n_small_n: int, k_large_n: int, n_large_n: int) -> dict:
    """The drop instrument: Newcombe-95 on (RR@min-N − RR@max-N). `positive` = the whole
    interval above zero — source_first genuinely fell as the source grew past the budget."""
    d, lo, hi = newcombe_diff(k_large_n, n_large_n, k_small_n, n_small_n)  # RR_small − RR_large
    return {"d": d, "lo": lo, "hi": hi, "positive": lo > 0.0}


def monotone_within_noise(cells_asc: list[tuple[int, int]]) -> bool:
    """A clean cliff is non-increasing as N GROWS. `cells_asc` is (k, n) in ASCENDING N;
    it holds unless some step RISES beyond noise (RR at the larger N significantly above
    the smaller — Newcombe excluding zero)."""
    for (k_s, n_s), (k_l, n_l) in zip(cells_asc, cells_asc[1:]):
        _d, lo, _hi = newcombe_diff(k_s, n_s, k_l, n_l)   # d = RR_large − RR_small
        if lo > 0.0:
            return False
    return True


def crossover_n(sf_cells_asc: list[dict]) -> int | None:
    """DESCRIPTIVE (never gated): the largest N at which source_first still reclaims above
    CROSSOVER_LEVEL — the boundary of the source-first law at this budget."""
    above = [c["N"] for c in sf_cells_asc if c["rate"] > CROSSOVER_LEVEL]
    return max(above) if above else None


def mechanism_gate(k_full: int, n_full: int, k_partial: int, n_partial: int) -> dict:
    """source_first reclaim split by whether the FULL source fit the budget (k==N) vs
    partial (k<N). full ≫ partial (Newcombe excluding zero) is the k<N information wall —
    the paper's mechanism: a sum needs every item."""
    d, lo, hi = newcombe_diff(k_partial, n_partial, k_full, n_full)   # RR_full − RR_partial
    return {"d": d, "lo": lo, "hi": hi, "positive": lo > 0.0,
            "full": (k_full, n_full), "partial": (k_partial, n_partial)}


def tracks_budget(crossovers: dict[int, int | None]) -> bool | None:
    """The paper's central claim: the crossover N is larger at the larger budget. Needs
    both budgets to have a defined crossover; None if it can't be evaluated."""
    pts = [(b, crossovers.get(b)) for b in sorted(crossovers)]
    if len(pts) < 2 or any(x is None for _, x in pts):
        return None
    return all(x_lo < x_hi for (_, x_lo), (_, x_hi) in zip(pts, pts[1:]))


def cliff_verdict(per_budget: dict, tracks: bool | None, mech_positive: bool | None,
                  confound_clean: bool = True) -> str:
    """D29's mapping, fixed before any data. per_budget[b] carries the booleans
    {ceiling, drop_positive, monotone, robust}. REPRODUCED needs the full paper pattern at
    both budgets plus the cross-budget crossover movement and the mechanism split; NULL is
    the pre-registered fix-is-robust verdict; else PARTIAL."""
    budgets = list(per_budget.values())
    if not budgets:
        return PARTIAL
    all_ceiling = all(b["ceiling"] for b in budgets)
    all_drop = all(b["drop_positive"] for b in budgets)
    all_monotone = all(b["monotone"] for b in budgets)
    no_drop = all(not b["drop_positive"] for b in budgets)
    all_robust = all(b["robust"] for b in budgets)
    if (all_ceiling and all_drop and all_monotone and tracks is True
            and mech_positive is True and confound_clean):
        return REPRODUCED
    if no_drop and all_robust:
        return NULL
    return PARTIAL


# ── the M5 problem schedule (D5: one fresh N-item receipt per trial, per source size) ─

def bank_problem(seed: int, n_items: int, trial: int) -> Problem:
    """Trial i's fresh N-item receipt on the M5 bank schedule for source size `n_items`
    (`m5g{seed}n{N}…` pids, disjoint from every v1/M4 namespace and across sizes)."""
    gen_seed = random.Random(f"m5-{seed}-N{n_items}-trial-{trial}").randrange(2 ** 31)
    return generate_sized(random.Random(gen_seed), f"m5g{seed}n{n_items}-{trial:02d}",
                          k_items=n_items)


def _load_problem(rec: dict) -> Problem:
    return Problem(**{**rec, "options": tuple(rec.get("options") or ())})


def _cell_key(n_items: int, budget: int, policy: str) -> str:
    return f"N{n_items}@B{budget}@{policy}"


def _cells_by_key(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(_cell_key(r["N"], r["budget"], r["policy"]), []).append(r)
    return out


# ── the trajectory banks (one per source size N; mirror m1/m4's arithmetic readout) ──

def run_bank(llm_for, target: int = N_BANK, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = M5_MODELS, ns: tuple[int, ...] = NS) -> dict[str, dict]:
    """Extend a bank of TAKEN trajectories per source size N until `target` took. Resume-aware
    and append-only. Carries a take-sanity read: v1 proved deepseek's arithmetic take
    (20/20), but multi-item receipts are new — a cratering take rate here is a signal caught
    before any grid spends (M0's kill-trigger philosophy, free)."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        per_n: dict[int, dict] = {}
        for n_items in ns:
            bank_dir = root / f"m5-bank-{key}-N{n_items}"
            bank_dir.mkdir(parents=True, exist_ok=True)
            results_path = bank_dir / "results.jsonl"
            rows = _read_jsonl(results_path)
            if rows and not rows[0]["pid"].startswith(f"m5g{seed}n{n_items}-"):
                raise ValueError(f"{results_path} carries pid {rows[0]['pid']!r} — a "
                                 f"different seed/size; refusing to mix schedules")
            takes = sum(r["took"] for r in rows)
            next_trial = len(rows)
            budget = 2 * max(0, target - takes) + 8
            while takes < target and budget > 0:
                problem = bank_problem(seed, n_items, next_trial)
                llm = llm_for(slug, problem)
                cost0 = getattr(llm, "cost", 0.0)
                trajectory = build_trajectory(llm, problem)
                reply = take_probe(llm, trajectory, problem)   # D11: never carried
                take = took(reply, problem)
                takes += take
                _write_trajectory(bank_dir / f"trial-{next_trial:02d}.jsonl", trajectory)
                row = {"trial": next_trial, "pid": problem.pid, "model": slug, "N": n_items,
                       "temperature": getattr(llm, "temperature", None),
                       "took": bool(take), "parsed": parse_answer(reply),
                       "take_reply": reply,
                       "cost": round(getattr(llm, "cost", 0.0) - cost0, 8),
                       "problem": asdict(problem)}
                rows.append(row)
                _append_jsonl(results_path, row)
                print(f"  [{key}] N={n_items} bank trial {next_trial:02d}: "
                      f"took={bool(take)} ({takes}/{target})", flush=True)
                next_trial += 1
                budget -= 1
            per_n[n_items] = {"trials": len(rows), "takes": takes,
                              "rate": takes / len(rows) if rows else 0.0,
                              "short": takes < target}
            print(f"  [{key}] N={n_items} bank: {takes}/{target} taken "
                  f"({per_n[n_items]['rate']:.0%})", flush=True)
        out[key] = {"label": f"m5-bank-{key}", "slug": slug, "per_n": per_n}
    return out


def load_bank(runs_root, key: str, n_items: int, seed: int = SEED) -> list[tuple[int, Problem]]:
    """The taken bank entries for source size N, in schedule order."""
    path = Path(runs_root) / f"m5-bank-{key}-N{n_items}" / "results.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no N={n_items} bank at {path} — run `uv run m5.py bank`")
    rows = _read_jsonl(path)
    if not rows:
        raise ValueError(f"{path} is empty — re-run the bank")
    return [(r["trial"], _load_problem(r["problem"])) for r in rows if r["took"]]


# ── the grid runner (N × budget × policy; one N-bank feeds both budgets and policies) ─

def run_grid(llm_for, n: int = N_CHECKPOINT, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = M5_MODELS, ns: tuple[int, ...] = NS,
             budgets: tuple[int, ...] = BUDGETS,
             policies: tuple[str, ...] = GRID_POLICIES) -> dict[str, dict]:
    """Extend every (N, budget, policy) cell to n trials over its N-bank, appending only the
    missing trials. Every note is graded-gated per trial before its token is spent
    (runner.run_session2_budget). D30 fixes N flat: no escalation."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        grid_dir = root / f"m5-grid-{key}"
        grid_dir.mkdir(parents=True, exist_ok=True)
        results_path = grid_dir / "results.jsonl"
        rows = _read_jsonl(results_path)
        done: dict[str, int] = {}
        for r in rows:
            ck = _cell_key(r["N"], r["budget"], r["policy"])
            done[ck] = done.get(ck, 0) + 1
        short = False
        for n_items in ns:
            bank = load_bank(root, key, n_items, seed)
            for budget in budgets:
                for policy in policies:
                    ck = _cell_key(n_items, budget, policy)
                    have = done.get(ck, 0)
                    want = min(n, len(bank))
                    if n > len(bank):
                        short = True
                    for t, problem in bank[have:want]:
                        llm = llm_for(slug, problem)
                        cost0 = getattr(llm, "cost", 0.0)
                        reply, note, k = run_session2_budget(llm, problem, budget, policy,
                                                             arm="directed")
                        g = grade(reply, problem)
                        _append_jsonl(results_path, {
                            "bank_trial": t, "pid": problem.pid, "N": n_items,
                            "budget": budget, "policy": policy, "k_kept": k,
                            "full_source": k == n_items, "note": note, "reply": reply,
                            "retained": round(retained_fraction(note, problem), 4),
                            "parsed": g.parsed, "hedged": g.hedged, "outcome": g.outcome,
                            "reclaimed": g.outcome == RECLAIMED, "model": slug,
                            "temperature": getattr(llm, "temperature", None),
                            "cost": round(getattr(llm, "cost", 0.0) - cost0, 8)})
                        print(f"  [{key}] {ck} trial {t:02d}: {g.outcome} "
                              f"(k={k}/{n_items})", flush=True)
        rows = _read_jsonl(results_path)
        cells = {ck: {"n": len(cr), "k": sum(r["reclaimed"] for r in cr)}
                 for ck, cr in _cells_by_key(rows).items()}
        out[key] = {"label": f"m5-grid-{key}", "slug": slug, "cells": cells, "short": short}
        print(f"  [{key}] grid: {len(cells)} cells"
              f"{' — SHORT BANK' if short else ''}", flush=True)
    return out


# ── the checkpoint and the judge — pure readers of the JSONL ─────────────────────────

def _outcome_counts(rows: list[dict]) -> dict[str, int]:
    counts = {o: 0 for o in OUTCOMES}
    for r in rows:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    return counts


def checkpoint(runs_root, models: dict[str, str] = M5_MODELS, sample_k: int = 3,
               rng_seed: int = 0) -> dict[str, dict]:
    """The scheduled N=20 interim look, $0. First job on the new note builder: bug-catch —
    a seeded ≥3-trial hand-read per cell (the budget-fit note, the graded retained fraction,
    the parsed outcome) AND the confound watch (is a source_first drop genuine
    recompute-failure — a silent mis-sum to the drift — or a truncation/gate bug?). The
    cliff trend is a LIGHT NOTE only; judging is once (D30)."""
    out: dict[str, dict] = {}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m5-grid-{key}" / "results.jsonl")
        cells: dict[str, dict] = {}
        for ck, cell_rows in _cells_by_key(rows).items():
            k = sum(r["reclaimed"] for r in cell_rows)
            rng = random.Random(f"{rng_seed}-{key}-{ck}")
            sample = rng.sample(cell_rows, min(sample_k, len(cell_rows)))
            cells[ck] = {"k": k, "n": len(cell_rows), "sample": sample,
                         "outcomes": _outcome_counts(cell_rows)}
        out[key] = {"cells": cells}
    return out


def judge(runs_root, models: dict[str, str] = M5_MODELS,
          confound_clean: bool = True) -> dict:
    """The D29 gate, $0, a pure function of the logged rows: per-cell Wilson + outcome
    split; per budget the source_first cliff over N (ceiling / drop / monotone / crossover);
    the cross-budget crossover-tracks-budget check; the pooled full-vs-partial mechanism
    split; the lossy_padded floor; and the pre-committed verdict."""
    result: dict = {"models": {}}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m5-grid-{key}" / "results.jsonl")
        cells: dict[str, dict] = {}
        for ck, cell_rows in _cells_by_key(rows).items():
            k, n = sum(r["reclaimed"] for r in cell_rows), len(cell_rows)
            lo, hi = wilson(k, n)
            r0 = cell_rows[0]
            cells[ck] = {"N": r0["N"], "budget": r0["budget"], "policy": r0["policy"],
                         "k": k, "n": n, "rate": k / n if n else 0.0,
                         "wilson_lo": lo, "wilson_hi": hi,
                         "outcomes": _outcome_counts(cell_rows)}
        per_budget: dict[int, dict] = {}
        crossovers: dict[int, int | None] = {}
        curves: dict[str, list[dict]] = {}
        for budget in sorted({c["budget"] for c in cells.values()}):
            for policy in GRID_POLICIES:
                curve = sorted((c for c in cells.values()
                                if c["budget"] == budget and c["policy"] == policy),
                               key=lambda c: c["N"])
                curves[f"B{budget}@{policy}"] = curve
            sf = curves[f"B{budget}@source_first"]
            if len(sf) >= 2:
                top, bot = sf[0], sf[-1]        # smallest N (source fits) → largest N (starved)
                drop = real_drop(top["k"], top["n"], bot["k"], bot["n"])
                per_budget[budget] = {
                    "ceiling": ceiling_intact(top["k"], top["n"]),
                    "drop": drop, "drop_positive": drop["positive"],
                    "monotone": monotone_within_noise([(c["k"], c["n"]) for c in sf]),
                    "robust": wilson(bot["k"], bot["n"])[0] >= ROBUST_FLOOR}
                crossovers[budget] = crossover_n(sf)
        # pooled full-vs-partial mechanism split, source_first only
        full = [r for r in rows if r["policy"] == "source_first" and r["full_source"]]
        part = [r for r in rows if r["policy"] == "source_first" and not r["full_source"]]
        mech = mechanism_gate(sum(r["reclaimed"] for r in full), len(full),
                              sum(r["reclaimed"] for r in part), len(part)) \
            if full and part else None
        tracks = tracks_budget(crossovers)
        verdict = cliff_verdict(per_budget, tracks,
                                mech["positive"] if mech else None, confound_clean) \
            if per_budget else None
        result["models"][key] = {
            "cells": cells, "curves": curves, "per_budget": per_budget,
            "crossovers": crossovers, "tracks_budget": tracks, "mechanism": mech,
            "verdict": verdict}
    return result


# ── the cliff figure (RR vs N per budget, the paper's shape) ─────────────────────────

FIGURE_PATH = Path("docs/figs/m5-boundary.png")


def make_figure(judged: dict, path=FIGURE_PATH) -> None:
    """One panel per model: source_first reclaim vs source size N, one curve per budget
    (log-x, the paper's shape), with the budget-matched lossy_padded floor dashed and the
    crossover marked — 'source-first leads until the source outgrows the budget.'"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = {k: m for k, m in judged["models"].items() if m["cells"]}
    ncols = max(1, len(models))
    fig, axes = plt.subplots(1, ncols, figsize=(6.0 * ncols, 4.6), squeeze=False)
    budget_colors = {BUDGETS[0]: "#1f77b4", BUDGETS[-1]: "#d62728"}
    for col, (key, m) in enumerate(models.items()):
        ax = axes[0][col]
        for budget in sorted({c["budget"] for c in m["cells"].values()}):
            color = budget_colors.get(budget, "#555555")
            sf = m["curves"].get(f"B{budget}@source_first", [])
            lp = m["curves"].get(f"B{budget}@lossy_padded", [])
            if sf:
                xs = [c["N"] for c in sf]
                ys = [c["rate"] for c in sf]
                lo = [max(0.0, c["rate"] - c["wilson_lo"]) for c in sf]
                hi = [max(0.0, c["wilson_hi"] - c["rate"]) for c in sf]
                ax.errorbar(xs, ys, yerr=[lo, hi], color=color, marker="o", ms=4,
                            capsize=3, label=f"source_first, B={budget}")
            if lp:
                ax.plot([c["N"] for c in lp], [c["rate"] for c in lp], color=color,
                        marker="x", ms=4, ls="--", alpha=0.6,
                        label=f"lossy_padded, B={budget}")
            xo = m["crossovers"].get(budget)
            if xo is not None:
                ax.axvline(xo, color=color, ls=":", alpha=0.5)
        ax.set_xscale("log")
        ax.set_xticks(NS)
        ax.set_xticklabels([str(n) for n in NS], fontsize=7)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("source size N (line items)")
        ax.set_title(f"{key}   verdict: {m['verdict']}")
        ax.grid(alpha=0.25)
        if col == 0:
            ax.set_ylabel("reclaim rate, directed")
            ax.legend(fontsize=7, loc="lower left")
    fig.suptitle("M5 — the source-size boundary: source-first leads until the source "
                 "outgrows the budget (Wilson 95%)")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ── CLI ──────────────────────────────────────────────────────────────────────────────

def _pick(arg: str | None) -> dict[str, str]:
    """Default to deepseek (D27); override to any single roster key."""
    if arg is None:
        return dict(M5_MODELS)
    if arg not in ROSTER:
        raise SystemExit(f"unknown model {arg!r}; roster keys: {', '.join(ROSTER)}")
    return {arg: ROSTER[arg]}


def main(argv: list[str]) -> int:
    cmds = ("bank", "grid", "checkpoint", "judge", "figure")
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "bank":
        target = int(argv[2]) if len(argv) > 2 else N_BANK
        models = _pick(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M5 bank: to {target} taken per source size N in {list(NS)}, depth 8, "
              f"temperature {TEMPERATURE}\n")
        run_bank(llm_for, target=target, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "grid":
        n = int(argv[2]) if len(argv) > 2 else N_CHECKPOINT
        models = _pick(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M5 grid: N={list(NS)} × budgets={list(BUDGETS)} × {list(GRID_POLICIES)} "
              f"to n={n} flat (D30), directed only, temperature {TEMPERATURE}\n")
        run_grid(llm_for, n=n, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "checkpoint":
        models = _pick(argv[2] if len(argv) > 2 else None)
        out = checkpoint("runs", models)
        for key, m in out.items():
            print(f"\n[{key}] checkpoint — hand-read the note builder first "
                  f"(budget-fit + graded gate + silent-mis-sum confound watch)")
            for ck, cell in sorted(m["cells"].items()):
                print(f"  {ck}: {cell['k']}/{cell['n']} reclaim | outcomes "
                      f"{cell['outcomes']}")
            for ck, cell in sorted(m["cells"].items()):
                print(f"\n  ── hand-read sample for {ck} "
                      f"({len(cell['sample'])} trials) " + "─" * 24)
                for r in cell["sample"]:
                    print(f"\n  trial {r['bank_trial']} {r['pid']} -> {r['outcome']} "
                          f"(k={r.get('k_kept')}/{r.get('N')}, parsed={r.get('parsed')}, "
                          f"retained={r.get('retained')})")
                    print(f"  NOTE : {r.get('note')}")
                    print(f"  REPLY: {r.get('reply')}")
        return 0

    if cmd == "judge":
        models = _pick(argv[2] if len(argv) > 2 else None)
        out = judge("runs", models)
        print("M5 judge — D29: gate the CLIFF's existence + direction per budget (ceiling, "
              "drop excludes zero, monotone), the crossover TRACKS the budget, and the "
              "full-vs-partial mechanism split; report crossover + floor. No DISCREPANT.\n")
        for key, m in out["models"].items():
            print(f"[{key}]  verdict: {m['verdict']}")
            for ck in sorted(m["cells"]):
                c = m["cells"][ck]
                print(f"  {ck:<26} {c['k']:>3}/{c['n']:<3} "
                      f"Wilson [{c['wilson_lo']:.1%}, {c['wilson_hi']:.1%}] "
                      f"outcomes {c['outcomes']}")
            for budget, pb in sorted(m["per_budget"].items()):
                d = pb["drop"]
                print(f"  B={budget}: ceiling={pb['ceiling']}  drop(RR@minN−RR@maxN)="
                      f"{d['d']:+.0%} [{d['lo']:+.1%},{d['hi']:+.1%}] "
                      f"{'EXCLUDES 0' if d['positive'] else 'includes 0'}  "
                      f"monotone={pb['monotone']}  crossover N={m['crossovers'].get(budget)}")
            print(f"  crossover tracks the budget: {m['tracks_budget']}")
            if m["mechanism"]:
                me = m["mechanism"]
                print(f"  mechanism (full k=N vs partial k<N): full {me['full'][0]}/"
                      f"{me['full'][1]} vs partial {me['partial'][0]}/{me['partial'][1]}"
                      f" → Δ{me['d']:+.0%} [{me['lo']:+.1%},{me['hi']:+.1%}] "
                      f"{'EXCLUDES 0' if me['positive'] else 'includes 0'}\n")
        return 0

    # figure
    models = _pick(argv[2] if len(argv) > 2 else None)
    out = judge("runs", models)
    make_figure(out, FIGURE_PATH)
    print(f"wrote {FIGURE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
