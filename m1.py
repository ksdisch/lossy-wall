"""m1.py — the M1 wall grid (bank → grid → checkpoint → judge → figure), with D14's
ladder pre-committed in code.

M1 measures KICKOFF claim 1 — the wall. Per model: 2 policies (lossy, source_first) ×
2 wall integrities (g = 0.1, 0.3), directed corrections only (D2). RR (reclaim rate) is
the fraction of session-2 trials the grader scores `reclaimed`. The claim's two
components, judged per (model, g) with the settled stats (D4): the lossy cell's Wilson
95% UPPER bound must sit at or under the 0.10 ceiling, and the Newcombe interval on
(source_first − lossy) must sit above zero. Both components at BOTH g clear a model;
v1 needs ≥2 cleared models (D14, DECISIONS.md).

The pipeline, free-before-paid (the brief's task order):

  bank — build the trajectory bank: session-1 trajectories on a fresh `m1-` problem
      schedule (D5: one fresh problem per trial, SHARED across models so differences
      are the model's, never the draw's; M0's pilot problems are not reused) until
      `target` trials TOOK (grader.took on the D11 take-probe turn, never carried).
      Resume-aware: re-running with a higher target EXTENDS the bank on the same
      schedule — it never re-runs or unlinks (the bank is a durable asset: its logged
      trajectories are M2's input — the g=1.0 lossy cell carries the full transcript).
  grid — run session-2 cells over the bank, in bank order, extending each cell to n
      trials without duplicates. source_first cells are capped at N_JUDGE (=40): no
      ceiling applies to them, so they never escalate (D14). Every note passes the
      per-trial source gate in the right direction before its trial spends a token
      (runner.verify_note_gate, inside run_session2).
  checkpoint — the scheduled N=20 interim look, $0: per cell, the futility screen
      (≥4 lossy reclaims → not-cleared, stop spending) and a seeded random sample of
      ≥3 trials for the MANDATORY hand-read (the M0 scoring lesson: two live bugs
      passed the anti-rig suite and were caught only by eyes on raw replies — eye
      source_first especially; the paper says RR 0.99–1.00, so a low reading means
      suspect OUR protocol first). Nothing can clear at 20 (0/20's bound is 16.1%).
  judge — the D14 ladder + Newcombe gaps + claim-1 composition, $0, a pure function
      of the logged rows. Also the replicate check: sf@0.1 and sf@0.3 are the SAME
      condition by construction (the g mapping is a threshold, so the note strings
      are identical) — if their rates disagree beyond noise, the run is broken.
  figure — RR vs g per model, Wilson bars, x-axis laid out for the full knob
      {0.1, 0.3, 0.6, 1.0} so M2's cells drop in without rework.

Sampling is D10's, imported from m0.py — never redefined here. The roster below is
D13's, frozen before the first grid call.

Run (paid steps gated on `uv run pytest` green, per the brief):
    uv run m1.py bank [target] [model]     # session-1 bank to `target` taken (default 40)
    uv run m1.py grid [n] [model]          # extend cells to n (default 20; sf capped at 40)
    uv run m1.py checkpoint [model]        # $0: futility + the hand-read sample
    uv run m1.py judge [model]             # $0: D14 ladder, gaps, claim-1 verdicts
    uv run m1.py figure                    # $0: docs/figs/m1-wall.png
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

from client import MODELS
from grader import grade, parse_answer, took
from m0 import MAX_TOKENS, SEED, TEMPERATURE, openrouter_factory
from notes import memory_note
from problems import Problem, generate
from runner import build_trajectory, run_session2, take_probe
from stats import excludes_zero, newcombe_diff, wilson

# ── the D13 roster (frozen before the first grid call) and the D14 constants ─────────

# D13 outcome (2026-07-06): the bounded re-attempt COMPLETED — 18/20 takes, D8 GREEN —
# so qwen72b joins. Labeled in every table as a same-family, 10×-size substitution for
# the paper's qwen-2.5-7b (D12), never as the paper's model. This constant IS the
# freeze: no roster change for the rest of M1.
ROSTER: dict[str, str] = {k: MODELS[k] for k in ("llama", "deepseek", "qwen72b")}

BANK_TARGET = 40      # the design N per model (D14's judge point)
GRID_G = (0.1, 0.3)   # the wall integrities (KICKOFF M1)
GRID_POLICIES = ("lossy", "source_first")

CEILING = 0.10        # D14: the lossy Wilson-95 upper-bound ceiling (D7's smallness scale)
N_CHECKPOINT = 20     # the scheduled interim look: hand-read + futility only
N_JUDGE = 40          # the gate's judge point; also the fixed sf cell size
N_MAX = 90            # the single pre-committed escalation's target
FUTILE_K = 4          # ≥4 reclaims is final anywhere: wilson(4, 90)[1] > CEILING


# ── the D14 ladder as a pure function (test_m1 pins the boundary arithmetic) ─────────

def lossy_cell_verdict(k: int, n: int) -> str:
    """One lossy cell's ladder state given k reclaims of n trials: 'continue' (below
    the judge point), 'cleared' / 'escalate' (at N_JUDGE), 'cleared' / 'not_cleared'
    (after the escalation — a short bank is judged at what it has: the ceiling is the
    pre-commitment, the N schedule is the spending plan)."""
    if k >= FUTILE_K:
        return "not_cleared"          # final anywhere: even 4/90 breaches the ceiling
    if n < N_JUDGE:
        return "continue"             # nothing can clear at the checkpoint
    if wilson(k, n)[1] <= CEILING:
        return "cleared"
    return "escalate" if n == N_JUDGE else "not_cleared"


def claim1_model_verdict(per_g: dict) -> str:
    """A model clears claim 1 only if BOTH components hold at BOTH g; one-g-only is
    PARTIAL (potential structure — where the wall starts — not a pass)."""
    passes = [per_g[g]["ceiling_cleared"] and per_g[g]["gap_positive"] for g in per_g]
    if all(passes):
        return "cleared"
    return "partial" if any(passes) else "not_cleared"


def claim1_v1_verdict(model_verdicts: list[str]) -> str:
    """v1 clears on ≥2 cleared models (KICKOFF's '≥2 of 3'; on a two-model roster that
    means both); exactly one is PARTIAL, reported plainly."""
    cleared = sum(v == "cleared" for v in model_verdicts)
    if cleared >= 2:
        return "cleared"
    return "partial" if cleared == 1 else "not_cleared"


# ── the m1- problem schedule (fresh, deterministic, shared across models) ────────────

def bank_problem(seed: int, trial: int) -> Problem:
    """Trial i's freshly generated problem on the M1 schedule — a different seed
    namespace than M0's `m0-…` keys, so no pilot problem is reused."""
    rng = random.Random(f"m1-{seed}-trial-{trial}")
    return generate(rng, f"m1g{seed}-{trial:02d}")


# ── JSONL plumbing (decay-pin convention, as in m0.py) ───────────────────────────────

def _append_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _write_trajectory(path: Path, messages: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for m in messages:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ── the trajectory bank ──────────────────────────────────────────────────────────────

def run_bank(llm_for, target: int = BANK_TARGET, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = ROSTER) -> dict[str, dict]:
    """Extend each model's bank until `target` trajectories TOOK. Resume-aware and
    append-only: existing rows are never re-run (the bank is a durable asset). A
    take-starved model stops at a bounded budget and reports `short` honestly."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        bank_dir = root / f"m1-bank-{key}"
        bank_dir.mkdir(parents=True, exist_ok=True)
        results_path = bank_dir / "results.jsonl"
        rows = _read_jsonl(results_path)
        if rows and not rows[0]["pid"].startswith(f"m1g{seed}-"):
            raise ValueError(f"{results_path} carries pid {rows[0]['pid']!r} — a "
                             f"different seed than {seed}; refusing to mix schedules")
        takes = sum(r["took"] for r in rows)
        next_trial = len(rows)
        budget = 2 * max(0, target - takes) + 8   # a low take rate can't loop forever
        while takes < target and budget > 0:
            problem = bank_problem(seed, next_trial)
            llm = llm_for(slug, problem)
            calls0 = getattr(llm, "calls", 0)
            cost0 = getattr(llm, "cost", 0.0)
            trajectory = build_trajectory(llm, problem)
            reply = take_probe(llm, trajectory)   # D11: measurement-only, never carried
            take = took(reply, problem)
            takes += take
            _write_trajectory(bank_dir / f"trial-{next_trial:02d}.jsonl", trajectory)
            row = {"trial": next_trial, "pid": problem.pid, "model": slug,
                   "temperature": getattr(llm, "temperature", None),
                   "took": bool(take), "parsed": parse_answer(reply),
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
        out[key] = {"label": f"m1-bank-{key}", "slug": slug, "trials": len(rows),
                    "takes": takes, "target": target, "short": takes < target}
        print(f"  [{key}] bank: {takes}/{target} taken in {len(rows)} trials"
              f"{' — SHORT' if out[key]['short'] else ''}", flush=True)
    return out


def load_bank(runs_root, key: str, seed: int = SEED) -> list[tuple[int, Problem]]:
    """The taken bank entries, in schedule order — what the grid consumes."""
    path = Path(runs_root) / f"m1-bank-{key}" / "results.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no bank at {path} — run `uv run m1.py bank` first")
    rows = _read_jsonl(path)
    if not rows:
        raise ValueError(f"{path} is empty — re-run the bank")
    if not rows[0]["pid"].startswith(f"m1g{seed}-"):
        raise ValueError(f"m1-bank-{key} rows carry pid {rows[0]['pid']!r} — a "
                         f"different seed than {seed}; the grid must consume the "
                         f"SAME schedule")
    return [(r["trial"], Problem(**r["problem"])) for r in rows if r["took"]]


# ── the grid runner ──────────────────────────────────────────────────────────────────

def _cell_key(policy: str, g: float) -> str:
    return f"{policy}@{g:g}"


def run_grid(llm_for, n: int = N_CHECKPOINT, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = ROSTER, gs: tuple[float, ...] = GRID_G,
             policies: tuple[str, ...] = GRID_POLICIES,
             sf_cap: int = N_JUDGE) -> dict[str, dict]:
    """Extend every (policy, g) cell to n trials over the bank, in bank order,
    appending only the missing trials (the ladder extends cells; nothing re-runs).
    source_first cells stop at `sf_cap` (D14: no ceiling, no escalation for sf)."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        bank = load_bank(root, key, seed)
        grid_dir = root / f"m1-grid-{key}"
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
                target_n = min(n, sf_cap) if policy == "source_first" else n
                have = done.get(ck, 0)
                want = min(target_n, len(bank))
                if target_n > len(bank):
                    short = True
                for t, problem in bank[have:want]:
                    llm = llm_for(slug, problem)
                    cost0 = getattr(llm, "cost", 0.0)
                    reply = run_session2(llm, problem, policy, g, arm="directed")
                    gr = grade(reply, problem)
                    _append_jsonl(results_path, {
                        "bank_trial": t, "pid": problem.pid, "policy": policy, "g": g,
                        "note": memory_note(problem, g, policy), "reply": reply,
                        "parsed": gr.parsed, "hedged": gr.hedged, "outcome": gr.outcome,
                        "reclaimed": gr.outcome == "reclaimed", "model": slug,
                        "temperature": getattr(llm, "temperature", None),
                        "cost": round(getattr(llm, "cost", 0.0) - cost0, 8)})
                    print(f"  [{key}] {ck} trial {t:02d} {problem.pid}: {gr.outcome}",
                          flush=True)
                cells[ck] = {"ran": max(0, want - have)}
        # recount k/n from the file — the single source of truth
        rows = _read_jsonl(results_path)
        for ck, cell in cells.items():
            cell_rows = [r for r in rows if _cell_key(r["policy"], r["g"]) == ck]
            cell["n"] = len(cell_rows)
            cell["k"] = sum(r["reclaimed"] for r in cell_rows)
        out[key] = {"label": f"m1-grid-{key}", "slug": slug, "cells": cells,
                    "short": short}
        summary = "  ".join(f"{ck} {c['k']}/{c['n']}" for ck, c in cells.items())
        print(f"  [{key}] grid: {summary}{' — SHORT BANK' if short else ''}", flush=True)
    return out


# ── the checkpoint (mechanical half) and the judge — pure readers of the JSONL ──────

def _cells_from_rows(rows: list[dict]) -> dict[str, list[dict]]:
    cells: dict[str, list[dict]] = {}
    for r in rows:
        cells.setdefault(_cell_key(r["policy"], r["g"]), []).append(r)
    return cells


def checkpoint(runs_root, models: dict[str, str] = ROSTER, sample_k: int = 3,
               rng_seed: int = 0) -> dict[str, dict]:
    """The scheduled N=20 interim look, $0: futility per lossy cell (≥FUTILE_K
    reclaims → stop spending) and a seeded random sample of `sample_k` trials per
    cell for the mandatory hand-read. No clearing power by construction."""
    out: dict[str, dict] = {}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m1-grid-{key}" / "results.jsonl")
        cells: dict[str, dict] = {}
        for ck, cell_rows in _cells_from_rows(rows).items():
            k = sum(r["reclaimed"] for r in cell_rows)
            rng = random.Random(f"{rng_seed}-{key}-{ck}")
            sample = rng.sample(cell_rows, min(sample_k, len(cell_rows)))
            cells[ck] = {"k": k, "n": len(cell_rows),
                         "futile": ck.startswith("lossy") and k >= FUTILE_K,
                         "sample": sample}
        out[key] = {"cells": cells,
                    "futile_cells": sorted(ck for ck, c in cells.items() if c["futile"])}
    return out


def judge(runs_root, models: dict[str, str] = ROSTER) -> dict:
    """The D14 gate, $0, a pure function of the logged rows: per-cell Wilson + ladder
    verdicts, per-g Newcombe gaps (base=lossy, mech=source_first), the claim-1
    composition, the sf replicate check, and the v1 verdict."""
    result: dict = {"models": {}}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m1-grid-{key}" / "results.jsonl")
        by_cell = _cells_from_rows(rows)
        cells: dict[str, dict] = {}
        for ck, cell_rows in by_cell.items():
            k, n = sum(r["reclaimed"] for r in cell_rows), len(cell_rows)
            lo, hi = wilson(k, n)
            cells[ck] = {"k": k, "n": n, "rate": k / n if n else 0.0,
                         "wilson_lo": lo, "wilson_hi": hi,
                         "verdict": lossy_cell_verdict(k, n)
                         if ck.startswith("lossy") else None}
        per_g: dict[str, dict] = {}
        gaps: dict[str, dict] = {}
        for g in GRID_G:
            lc, sc = cells.get(_cell_key("lossy", g)), cells.get(
                _cell_key("source_first", g))
            if lc is None or sc is None:
                continue
            d, lo, hi = newcombe_diff(lc["k"], lc["n"], sc["k"], sc["n"])
            gaps[f"{g:g}"] = {"d": d, "lo": lo, "hi": hi}
            per_g[f"{g:g}"] = {"ceiling_cleared": lc["verdict"] == "cleared",
                               "gap_positive": lo > 0.0}
            per_g[f"{g:g}"]["passes"] = (per_g[f"{g:g}"]["ceiling_cleared"]
                                         and per_g[f"{g:g}"]["gap_positive"])
        # the replicate check: sf@0.1 and sf@0.3 are the same note string by the
        # g-threshold mapping — disagreement beyond noise means the run is broken
        replicate = None
        s1, s3 = cells.get("source_first@0.1"), cells.get("source_first@0.3")
        if s1 and s3:
            d, lo, hi = newcombe_diff(s1["k"], s1["n"], s3["k"], s3["n"])
            replicate = {"d": d, "lo": lo, "hi": hi,
                         "consistent": not excludes_zero(lo, hi)}
        verdict = claim1_model_verdict(
            {g: per_g[f"{g:g}"] for g in GRID_G if f"{g:g}" in per_g}) if per_g else None
        result["models"][key] = {"cells": cells, "gaps": gaps, "per_g": per_g,
                                 "verdict": verdict, "replicate": replicate}
    result["v1"] = claim1_v1_verdict(
        [m["verdict"] for m in result["models"].values() if m["verdict"]])
    return result


# ── the wall figure ──────────────────────────────────────────────────────────────────

FIGURE_PATH = Path("docs/figs/m1-wall.png")
KNOB_AXIS = (0.1, 0.3, 0.6, 1.0)   # the full v1 knob: M2's cells drop into this axis


def make_figure(judged: dict, path=FIGURE_PATH) -> None:
    """RR vs g, one panel per model, two series with Wilson 95% bars and per-point N —
    the wall figure the milestone commits (docs/figs/m1-wall.png)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = judged["models"]
    fig, axes = plt.subplots(1, max(1, len(models)), sharey=True,
                             figsize=(5.2 * max(1, len(models)), 4.2), squeeze=False)
    for ax, (key, m) in zip(axes[0], models.items()):
        for policy, color, marker in (("lossy", "#c0392b", "o"),
                                      ("source_first", "#2471a3", "s")):
            xs, ys, lo_err, hi_err, ns = [], [], [], [], []
            for g in KNOB_AXIS:
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
                dy = -14 if y > 0.9 else 6   # points at the ceiling annotate below
                ax.annotate(f"n={n}", (x, y), textcoords="offset points",
                            xytext=(6, dy), fontsize=8, color=color)
        ax.set_xticks(KNOB_AXIS)
        ax.set_xlim(0.0, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("note integrity g")
        ax.set_title(key)
        ax.grid(alpha=0.25)
    axes[0][0].set_ylabel("reclaim rate (directed correction)")
    axes[0][0].legend(loc="center right")
    fig.suptitle("M1 — the wall: reclaim rate vs note integrity (Wilson 95%)")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ── CLI ──────────────────────────────────────────────────────────────────────────────

def _pick_models(model_key: str | None) -> dict[str, str]:
    if model_key is None:
        return dict(ROSTER)
    if model_key not in ROSTER:
        raise SystemExit(f"unknown roster key {model_key!r} (roster: {', '.join(ROSTER)})")
    return {model_key: ROSTER[model_key]}


def _print_cost(cache) -> None:
    for slug, m in cache.items():
        print(f"  {slug}: {m.calls} calls, {m.prompt_tokens} prompt + "
              f"{m.completion_tokens} completion tokens, cost ${m.cost:.6f}")
    print(f"  measured total this command: ${sum(m.cost for m in cache.values()):.6f}")


def main(argv: list[str]) -> int:
    cmds = ("bank", "grid", "checkpoint", "judge", "figure")
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "bank":
        target = int(argv[2]) if len(argv) > 2 else BANK_TARGET
        models = _pick_models(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M1 bank: to {target} taken/model, depth 8, temperature {TEMPERATURE}\n")
        run_bank(llm_for, target=target, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "grid":
        n = int(argv[2]) if len(argv) > 2 else N_CHECKPOINT
        models = _pick_models(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M1 grid: cells to n={n} (sf capped at {N_JUDGE}), directed only, "
              f"temperature {TEMPERATURE}\n")
        run_grid(llm_for, n=n, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "checkpoint":
        models = _pick_models(argv[2] if len(argv) > 2 else None)
        out = checkpoint("runs", models)
        for key, m in out.items():
            print(f"\n[{key}] checkpoint — futility screen + hand-read sample")
            for ck, cell in sorted(m["cells"].items()):
                flag = "  FUTILE (>=4 reclaims: stop spending)" if cell["futile"] else ""
                print(f"  {ck}: {cell['k']}/{cell['n']} reclaimed{flag}")
            for ck, cell in sorted(m["cells"].items()):
                print(f"\n  ── hand-read sample for {ck} "
                      f"({len(cell['sample'])} trials) " + "─" * 30)
                for r in cell["sample"]:
                    print(f"\n  trial {r['bank_trial']} {r['pid']} -> {r['outcome']}"
                          f" (parsed={r['parsed']}, hedged={r['hedged']})")
                    print(f"  NOTE : {r['note']}")
                    print(f"  REPLY: {r['reply']}")
        return 0

    if cmd == "judge":
        models = _pick_models(argv[2] if len(argv) > 2 else None)
        out = judge("runs", models)
        print("M1 judge — the D14 gate (ceiling 0.10 on the lossy Wilson-95 upper "
              "bound; Newcombe gap above zero; both g)\n")
        for key, m in out["models"].items():
            print(f"[{key}]")
            for ck, cell in sorted(m["cells"].items()):
                v = f"  -> {cell['verdict']}" if cell["verdict"] else ""
                print(f"  {ck:<20} {cell['k']:>3}/{cell['n']:<3} "
                      f"Wilson [{cell['wilson_lo']:.1%}, {cell['wilson_hi']:.1%}]{v}")
            for g, gap in m["gaps"].items():
                print(f"  gap (sf - lossy) @ g={g}: {gap['d']:+.0%} "
                      f"Newcombe [{gap['lo']:+.1%}, {gap['hi']:+.1%}]")
            if m["replicate"]:
                r = m["replicate"]
                tag = "consistent" if r["consistent"] else "INCONSISTENT — stop and look"
                print(f"  sf replicate check (0.3 vs 0.1): {r['d']:+.0%} "
                      f"[{r['lo']:+.1%}, {r['hi']:+.1%}] — {tag}")
            print(f"  model verdict: {m['verdict']}\n")
        print(f"v1 claim-1 verdict: {out['v1']}")
        return 0

    # figure
    out = judge("runs", dict(ROSTER))
    make_figure(out, FIGURE_PATH)
    print(f"wrote {FIGURE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
