"""m2.py — the M2 controls grid (grid → checkpoint → judge → figures) over M1's banks,
with D16's containment ladder and D17's blind-committed counting rule in code.

M2 runs the controls that make claim 1 mean what it says, plus the cells that complete
the figure — seven new cells per model (+ blank on deepseek), ZERO re-runs of judged
M1 cells (D14's judged-once; M1's archived cells are the comparators):

  claim 2 (content, not length) — lossy_padded at both wall g: the same lossy note,
      padded with content-free filler to the source_first note's length (the budget-
      match control). Two components per (model, g), judged against M1's archived
      cells: EQUIVALENCE — the Newcombe 95% interval on (lossy_padded − lossy) sits
      entirely inside ±δ = ±0.10 (D7's containment gate; judged at N=40, one
      escalation to ≈90, comparator-dependent so NO fixed futility cutoff exists) —
      and SEPARATION — the interval on (source_first − lossy_padded) excludes zero.
      Composition mirrors D14: both components at BOTH wall g clear a model; v1 needs
      ≥2 of 3 (the rollup is claim 1's own, imported).
  claim 3 (worse than empty — the title claim) — deepseek only: a blank note at N=40
      over the same bank vs M1's ARCHIVED lossy@0.1 rows (n=90). Counting rule,
      committed blind 2026-07-07 while the archived split was untallied: wrong
      emission iff the logged outcome is emit_attractor/emit_other_wrong; gate = the
      Newcombe interval on wrong-emission (lossy − blank) excludes zero. The judge
      enforces the no-peek pledge mechanically: it refuses to tally either arm until
      the blank cell has reached its final N.
  the knob fills (descriptive, D18) — lossy and source_first at g ∈ {0.6, 1.0}, N=40
      uniform, all three models: the top of the curve for the committed figure. They
      gate nothing. lossy@1.0 is the TRANSCRIPT cell — their runner's verbatim special
      case where the full session-1 conversation survives instead of a note — loaded
      from the bank's trial files. sf@0.6 ≡ sf@1.0 are the identical note string
      (threshold mapping): a free replicate pair, checked in the judge.

Everything paid runs over `m1.load_bank`'s taken trials in bank order (D5's pairing:
every cell sees the same trajectories, so policies differ by the note alone). Sampling
is D10's, imported via m0; roster and N schedule are m1's, imported, never redefined.

Run (paid steps gated on `uv run pytest` green, per the brief):
    uv run m2.py grid [n] [model]     # extend M2 cells to n (knob/blank cap 40; padded to 90)
    uv run m2.py checkpoint [model]   # $0: counts + the hand-read sample (no futility — D16)
    uv run m2.py judge [model]        # $0: ladder, claim-2/claim-3 verdicts, replicate
    uv run m2.py figures              # $0: docs/figs/m2-knob.png + m2-emission.png
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from grader import ABSTAIN, EMIT_ATTRACTOR, EMIT_OTHER, RECLAIMED, emitted_wrong, grade
from m0 import MAX_TOKENS, SEED, TEMPERATURE, openrouter_factory
from m1 import (KNOB_AXIS, N_CHECKPOINT, N_JUDGE, N_MAX, ROSTER, _append_jsonl,
                _cell_key, _cells_from_rows, _pick_models, _print_cost, _read_jsonl,
                bank_problem, load_bank)
from m1 import claim1_v1_verdict as claim2_v1_verdict  # the ≥2-of-3 rollup IS D14's
from notes import memory_note
from runner import reclaim_cross, run_session2
from stats import excludes_zero, newcombe_diff, wilson

# ── the D16/D17/D18 constants (δ is D7's, committed at the M0 sign-off) ──────────────

DELTA = 0.10                    # D7: the equivalence margin ±δ, fixed before any data
PADDED_G = (0.1, 0.3)           # claim 2 runs at both wall integrities (D16)
KNOB_G = (0.6, 1.0)             # the descriptive fills (D18); 1.0 = the transcript cell
KNOB_POLICIES = ("lossy", "source_first")
BLANK_MODELS = ("deepseek",)    # the roster's only emitter (D17); llama/qwen72b keep
                                # their recorded probe NULLs (D9/D13, rider (a) = no)
BLANK_G = 0.1                   # blank is g-independent; logged at the wall locus

KNOB_FIGURE_PATH = Path("docs/figs/m2-knob.png")
EMISSION_FIGURE_PATH = Path("docs/figs/m2-emission.png")   # m1-wall.png stays untouched


def cell_plan(key: str, blank_models: tuple[str, ...] = BLANK_MODELS) -> list[tuple[str, float]]:
    """The (policy, g) cells M2 runs for one model: 2 padded + 4 knob everywhere,
    + blank on the emitter(s) only."""
    cells = [("lossy_padded", g) for g in PADDED_G]
    cells += [(p, g) for p in KNOB_POLICIES for g in KNOB_G]
    if key in blank_models:
        cells.append(("blank", BLANK_G))
    return cells


# ── the D16 containment ladder as a pure function (test_m2 pins the arithmetic) ──────

def padded_cell_verdict(k_pad: int, n_pad: int, k_cmp: int, n_cmp: int) -> str:
    """One padded cell's ladder state against its ARCHIVED lossy comparator:
    'continue' below the judge point (no futility shortcut exists — the containment
    boundary is comparator-dependent, e.g. 4/90 fails vs a 0/40 comparator at +10.9%
    but clears vs 1/90 at +9.8%); at N_JUDGE, contained inside ±DELTA → 'contained',
    else 'escalate' (once, to ≈90); past N_JUDGE the cell is judged at whatever n it
    reached — 'contained' or 'not_contained', final."""
    if n_pad < N_JUDGE:
        return "continue"
    _, lo, hi = newcombe_diff(k_cmp, n_cmp, k_pad, n_pad)   # d = padded − lossy
    if -DELTA < lo and hi < DELTA:
        return "contained"
    return "escalate" if n_pad == N_JUDGE else "not_contained"


def claim2_model_verdict(per_g: dict) -> str:
    """A model clears claim 2 only if BOTH components (containment + separation) hold
    at BOTH wall g; one-g-only is PARTIAL — the D14 composition, mirrored (D16)."""
    passes = [per_g[g]["contained"] and per_g[g]["separated"] for g in per_g]
    if all(passes):
        return "cleared"
    return "partial" if any(passes) else "not_cleared"


# ── claim 3's counter and gate (the rule committed blind, D17) ───────────────────────

def emission_split(rows: list[dict]) -> dict:
    """The abstain-vs-emit tally over logged rows — the counting rule as committed:
    a wrong emission iff the outcome is emit_attractor or emit_other_wrong
    (grader.emitted_wrong's rule applied to the logged outcome strings)."""
    o = [r["outcome"] for r in rows]
    att, other = o.count(EMIT_ATTRACTOR), o.count(EMIT_OTHER)
    return {"n": len(o), "wrong": att + other, "attractor": att, "other_wrong": other,
            "abstain": o.count(ABSTAIN), "reclaimed": o.count(RECLAIMED)}


def claim3_verdict(k_lossy: int, n_lossy: int, k_blank: int, n_blank: int) -> dict:
    """The gate: the Newcombe 95% interval on wrong-emission rate (lossy − blank)
    excludes zero (base=blank, mech=lossy — the stats.py convention)."""
    d, lo, hi = newcombe_diff(k_blank, n_blank, k_lossy, n_lossy)
    return {"d": d, "lo": lo, "hi": hi, "cleared": excludes_zero(lo, hi)}


# ── the transcript loader (the g=1.0 lossy cell carries the full session 1) ─────────

def load_trajectory(runs_root, key: str, trial: int) -> list[dict]:
    """One bank trial's full session-1 message list, from the bank's trial file —
    what the transcript cell carries instead of a note."""
    path = Path(runs_root) / f"m1-bank-{key}" / f"trial-{trial:02d}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no bank trajectory at {path} — the transcript cell "
                                f"needs m1's bank files")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ── the grid runner ──────────────────────────────────────────────────────────────────

def run_grid(llm_for, n: int = N_CHECKPOINT, seed: int = SEED, runs_root="runs",
             models: dict[str, str] = ROSTER,
             blank_models: tuple[str, ...] = BLANK_MODELS,
             knob_cap: int = N_JUDGE, pad_cap: int = N_MAX) -> dict[str, dict]:
    """Extend every M2 cell to n trials over the m1 bank, in bank order, appending
    only the missing trials (nothing re-runs). Knob and blank cells stop at
    `knob_cap` (D18/D17 fix them at N=40 — no ladder); only padded cells may extend
    toward `pad_cap` (the D16 ladder's single escalation). Every note passes the
    per-trial source gate inside run_session2; the transcript cell is gated on the
    original question being present in the carried session-1 conversation."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        bank = load_bank(root, key, seed)
        grid_dir = root / f"m2-grid-{key}"
        grid_dir.mkdir(parents=True, exist_ok=True)
        results_path = grid_dir / "results.jsonl"
        rows = _read_jsonl(results_path)
        done: dict[str, int] = {}
        for r in rows:
            ck = _cell_key(r["policy"], r["g"])
            done[ck] = done.get(ck, 0) + 1
        cells: dict[str, dict] = {}
        short = False
        for policy, g in cell_plan(key, blank_models):
            ck = _cell_key(policy, g)
            cap = pad_cap if policy == "lossy_padded" else knob_cap
            target_n = min(n, cap)
            have = done.get(ck, 0)
            want = min(target_n, len(bank))
            if target_n > len(bank):
                short = True
            for t, problem in bank[have:want]:
                llm = llm_for(slug, problem)
                cost0 = getattr(llm, "cost", 0.0)
                transcript = (load_trajectory(root, key, t)
                              if policy == "lossy" and g >= 0.99 else None)
                reply = run_session2(llm, problem, policy, g, arm="directed",
                                     transcript=transcript)
                gr = grade(reply, problem)
                row = {"bank_trial": t, "pid": problem.pid, "policy": policy, "g": g,
                       "note": None if transcript else memory_note(problem, g, policy),
                       "reply": reply, "parsed": gr.parsed, "hedged": gr.hedged,
                       "outcome": gr.outcome, "reclaimed": gr.outcome == RECLAIMED,
                       "wrong": emitted_wrong(gr), "model": slug,
                       "temperature": getattr(llm, "temperature", None),
                       "cost": round(getattr(llm, "cost", 0.0) - cost0, 8)}
                if transcript:
                    row["transcript_turns"] = len(transcript)
                _append_jsonl(results_path, row)
                print(f"  [{key}] {ck} trial {t:02d} {problem.pid}: {gr.outcome}",
                      flush=True)
            cells[ck] = {"ran": max(0, want - have)}
        # recount k/n from the file — the single source of truth
        rows = _read_jsonl(results_path)
        for ck, cell in cells.items():
            cell_rows = [r for r in rows if _cell_key(r["policy"], r["g"]) == ck]
            cell["n"] = len(cell_rows)
            cell["k"] = sum(r["reclaimed"] for r in cell_rows)
        out[key] = {"label": f"m2-grid-{key}", "slug": slug, "cells": cells,
                    "short": short}
        summary = "  ".join(f"{ck} {c['k']}/{c['n']}" for ck, c in cells.items())
        print(f"  [{key}] grid: {summary}{' — SHORT BANK' if short else ''}", flush=True)
    return out


# ── the checkpoint (mechanical half) — counts + the hand-read sample, NO futility ────

def checkpoint(runs_root, models: dict[str, str] = ROSTER, sample_k: int = 3,
               rng_seed: int = 0) -> dict[str, dict]:
    """The scheduled N=20 interim look, $0: per-cell counts and a seeded random
    sample of `sample_k` trials for the MANDATORY hand-read. No futility screen by
    design (D16): none of M2's cells carries a reclaim ceiling, and the containment
    boundary is comparator-dependent — the checkpoint's power here is the eyes."""
    out: dict[str, dict] = {}
    for key in models:
        rows = _read_jsonl(Path(runs_root) / f"m2-grid-{key}" / "results.jsonl")
        cells: dict[str, dict] = {}
        for ck, cell_rows in _cells_from_rows(rows).items():
            rng = random.Random(f"{rng_seed}-{key}-{ck}")
            sample = rng.sample(cell_rows, min(sample_k, len(cell_rows)))
            cells[ck] = {"k": sum(r["reclaimed"] for r in cell_rows),
                         "n": len(cell_rows), "sample": sample}
        out[key] = {"cells": cells}
    return out


# ── the judge — a pure function of the m1 (comparator) + m2 logged rows ──────────────

def judge(runs_root, models: dict[str, str] = ROSTER) -> dict:
    """The pre-committed gates, $0: the D16 ladder + separation per wall g against
    M1's archived cells, the claim-2 composition, claim 3 counted once (both arms,
    only after blank reaches its final N — the no-peek pledge held mechanically),
    the sf@0.6 ≡ sf@1.0 replicate check, and the merged cell table for the figure."""
    result: dict = {"models": {}}
    for key in models:
        m1_rows = _read_jsonl(Path(runs_root) / f"m1-grid-{key}" / "results.jsonl")
        m2_rows = _read_jsonl(Path(runs_root) / f"m2-grid-{key}" / "results.jsonl")
        by_cell = _cells_from_rows(m1_rows)
        by_cell.update(_cells_from_rows(m2_rows))   # no collisions: M2 re-runs nothing
        cells: dict[str, dict] = {}
        for ck, cell_rows in by_cell.items():
            k, n = sum(r["reclaimed"] for r in cell_rows), len(cell_rows)
            lo, hi = wilson(k, n)
            cells[ck] = {"k": k, "n": n, "rate": k / n if n else 0.0,
                         "wilson_lo": lo, "wilson_hi": hi}
        # claim 2, per wall g against the archived comparators
        per_g: dict[str, dict] = {}
        for g in PADDED_G:
            pad = cells.get(_cell_key("lossy_padded", g))
            lc = cells.get(_cell_key("lossy", g))
            sc = cells.get(_cell_key("source_first", g))
            if pad is None or lc is None or sc is None:
                continue
            ev = padded_cell_verdict(pad["k"], pad["n"], lc["k"], lc["n"])
            d_e, lo_e, hi_e = newcombe_diff(lc["k"], lc["n"], pad["k"], pad["n"])
            d_s, lo_s, hi_s = newcombe_diff(pad["k"], pad["n"], sc["k"], sc["n"])
            entry = {"equivalence": {"d": d_e, "lo": lo_e, "hi": hi_e, "verdict": ev},
                     "separation": {"d": d_s, "lo": lo_s, "hi": hi_s},
                     "contained": ev == "contained",
                     "separated": excludes_zero(lo_s, hi_s)}
            entry["passes"] = entry["contained"] and entry["separated"]
            per_g[f"{g:g}"] = entry
        c2_verdict = claim2_model_verdict(
            {g: per_g[f"{g:g}"] for g in PADDED_G if f"{g:g}" in per_g}) if per_g else None
        # claim 3: counted once, at judge time, after blank reaches its final N
        blank_rows = [r for r in m2_rows if r["policy"] == "blank"]
        claim3 = None
        if blank_rows and len(blank_rows) < N_JUDGE:
            claim3 = {"pending": True, "blank_n": len(blank_rows)}
        elif blank_rows:
            lossy_rows = [r for r in m1_rows
                          if r["policy"] == "lossy" and r["g"] == BLANK_G]
            l_split, b_split = emission_split(lossy_rows), emission_split(blank_rows)
            claim3 = {"lossy": l_split, "blank": b_split,
                      **claim3_verdict(l_split["wrong"], l_split["n"],
                                       b_split["wrong"], b_split["n"])}
        # the replicate check: sf@0.6 and sf@1.0 are the SAME note string (threshold
        # mapping) — disagreement beyond noise means the run is broken
        replicate = None
        s6 = cells.get(_cell_key("source_first", 0.6))
        s10 = cells.get(_cell_key("source_first", 1.0))
        if s6 and s10:
            d, lo, hi = newcombe_diff(s6["k"], s6["n"], s10["k"], s10["n"])
            replicate = {"d": d, "lo": lo, "hi": hi,
                         "consistent": not excludes_zero(lo, hi)}
        result["models"][key] = {"cells": cells,
                                 "claim2": {"per_g": per_g, "verdict": c2_verdict},
                                 "claim3": claim3, "replicate": replicate}
    result["claim2_v1"] = claim2_v1_verdict(
        [m["claim2"]["verdict"] for m in result["models"].values()
         if m["claim2"]["verdict"]])
    return result


# ── the figures ──────────────────────────────────────────────────────────────────────

def make_knob_figure(judged: dict, path=KNOB_FIGURE_PATH) -> None:
    """The capstone knob: RR vs g per model across the full axis {0.1, 0.3, 0.6, 1.0}
    (M1's wall cells + M2's fills), padded points at the wall, blank's reclaim point
    where it ran — Wilson 95% bars, per-point N (docs/figs/m2-knob.png)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = judged["models"]
    fig, axes = plt.subplots(1, max(1, len(models)), sharey=True,
                             figsize=(5.2 * max(1, len(models)), 4.2), squeeze=False)
    for ax, (key, m) in zip(axes[0], models.items()):
        for policy, color, marker in (("lossy", "#c0392b", "o"),
                                      ("source_first", "#2471a3", "s"),
                                      ("lossy_padded", "#e67e22", "D")):
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
            if not xs:
                continue
            ax.errorbar(xs, ys, yerr=[lo_err, hi_err], color=color, marker=marker,
                        capsize=4, label=policy)
            for x, y, n in zip(xs, ys, ns):
                dy = -14 if y > 0.9 else 6   # points at the ceiling annotate below
                ax.annotate(f"n={n}", (x, y), textcoords="offset points",
                            xytext=(6, dy), fontsize=8, color=color)
        blank = m["cells"].get(_cell_key("blank", BLANK_G))
        if blank:
            ax.errorbar([BLANK_G], [blank["rate"]],
                        yerr=[[blank["rate"] - blank["wilson_lo"]],
                              [blank["wilson_hi"] - blank["rate"]]],
                        color="#27ae60", marker="^", capsize=4, linestyle="none",
                        label="blank")
            ax.annotate(f"n={blank['n']}", (BLANK_G, blank["rate"]),
                        textcoords="offset points", xytext=(6, 6), fontsize=8,
                        color="#27ae60")
        ax.set_xticks(KNOB_AXIS)
        ax.set_xlim(0.0, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("note integrity g")
        ax.set_title(key)
        ax.grid(alpha=0.25)
    axes[0][0].set_ylabel("reclaim rate (directed correction)")
    axes[0][0].legend(loc="center right")
    fig.suptitle("M2 — the full knob: reclaim rate vs note integrity (Wilson 95%)")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_emission_figure(judged: dict, path=EMISSION_FIGURE_PATH) -> None:
    """Claim 3's picture: wrong-emission rate, lossy vs blank, Wilson 95% bars,
    counts annotated — one panel per model with a judged blank arm
    (docs/figs/m2-emission.png)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = {k: m for k, m in judged["models"].items()
              if m.get("claim3") and not m["claim3"].get("pending")}
    fig, axes = plt.subplots(1, max(1, len(models)),
                             figsize=(4.6 * max(1, len(models)), 4.2), squeeze=False)
    for ax, (key, m) in zip(axes[0], models.items()):
        c3 = m["claim3"]
        for x, (arm, color) in enumerate((("lossy", "#c0392b"), ("blank", "#7f8c8d"))):
            s = c3[arm]
            rate = s["wrong"] / s["n"] if s["n"] else 0.0
            lo, hi = wilson(s["wrong"], s["n"])
            ax.bar(x, rate, color=color, width=0.6)
            ax.errorbar(x, rate, yerr=[[rate - lo], [hi - rate]], color="black",
                        capsize=5)
            ax.annotate(f"{s['wrong']}/{s['n']}", (x, rate),
                        textcoords="offset points", xytext=(0, 8), ha="center",
                        fontsize=9)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"lossy@{BLANK_G:g}", "blank"])
        ax.set_ylim(0.0, 1.05)
        ax.set_title(key)
        ax.grid(alpha=0.25, axis="y")
    axes[0][0].set_ylabel("wrong-emission rate")
    fig.suptitle("M2 — worse than empty (Wilson 95%)")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ── CLI ──────────────────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    cmds = ("grid", "checkpoint", "judge", "figures")
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "grid":
        n = int(argv[2]) if len(argv) > 2 else N_CHECKPOINT
        models = _pick_models(argv[3] if len(argv) > 3 else None)
        llm_for, cache = openrouter_factory()
        print(f"M2 grid: cells to n={n} (knob/blank capped at {N_JUDGE}, padded "
              f"ladder to {N_MAX}), directed only, temperature {TEMPERATURE}\n")
        run_grid(llm_for, n=n, models=models)
        print("\ncost (OpenRouter-measured, usage.include):")
        _print_cost(cache)
        return 0

    if cmd == "checkpoint":
        models = _pick_models(argv[2] if len(argv) > 2 else None)
        out = checkpoint("runs", models)
        for key, m in out.items():
            print(f"\n[{key}] checkpoint — counts + hand-read sample "
                  f"(no futility: D16)")
            for ck, cell in sorted(m["cells"].items()):
                print(f"  {ck}: {cell['k']}/{cell['n']} reclaimed")
            for ck, cell in sorted(m["cells"].items()):
                print(f"\n  ── hand-read sample for {ck} "
                      f"({len(cell['sample'])} trials) " + "─" * 30)
                for r in cell["sample"]:
                    print(f"\n  trial {r['bank_trial']} {r['pid']} -> {r['outcome']}"
                          f" (parsed={r['parsed']}, hedged={r['hedged']})")
                    if r["note"] is None:
                        # the transcript cell: eyes on the ASSEMBLED context
                        traj = load_trajectory("runs", key, r["bank_trial"])
                        problem = bank_problem(SEED, r["bank_trial"])
                        print(f"  TRANSCRIPT ({len(traj)} turns, in full):")
                        for msg in traj:
                            print(f"    [{msg['role']}] {msg['content']}")
                        print(f"  CORRECTION: {reclaim_cross(problem)}")
                    else:
                        print(f"  NOTE : {r['note']}")
                    print(f"  REPLY: {r['reply']}")
        return 0

    if cmd == "judge":
        models = _pick_models(argv[2] if len(argv) > 2 else None)
        out = judge("runs", models)
        print("M2 judge — D16's containment ladder (±10% on lossy_padded − lossy; "
              "separation excludes zero; both wall g) + D17's emission gate\n")
        for key, m in out["models"].items():
            print(f"[{key}]")
            for ck, cell in sorted(m["cells"].items()):
                print(f"  {ck:<20} {cell['k']:>3}/{cell['n']:<3} "
                      f"Wilson [{cell['wilson_lo']:.1%}, {cell['wilson_hi']:.1%}]")
            for g, pg in m["claim2"]["per_g"].items():
                e, s = pg["equivalence"], pg["separation"]
                print(f"  claim 2 @ g={g}: equivalence (padded - lossy) {e['d']:+.0%} "
                      f"[{e['lo']:+.1%}, {e['hi']:+.1%}] -> {e['verdict']}")
                print(f"                separation (sf - padded) {s['d']:+.0%} "
                      f"[{s['lo']:+.1%}, {s['hi']:+.1%}] -> "
                      f"{'holds' if pg['separated'] else 'fails'}")
            print(f"  claim-2 model verdict: {m['claim2']['verdict']}")
            if m["claim3"] is not None:
                c3 = m["claim3"]
                if c3.get("pending"):
                    print(f"  claim 3: PENDING — blank at n={c3['blank_n']} < "
                          f"{N_JUDGE}; arms stay untallied (no-peek)")
                else:
                    for arm in ("lossy", "blank"):
                        s = c3[arm]
                        print(f"  claim 3 {arm}: wrong {s['wrong']}/{s['n']} "
                              f"(attractor {s['attractor']}, other {s['other_wrong']}, "
                              f"abstain {s['abstain']}, reclaimed {s['reclaimed']})")
                    print(f"  claim 3 gap (lossy - blank): {c3['d']:+.0%} "
                          f"[{c3['lo']:+.1%}, {c3['hi']:+.1%}] -> "
                          f"{'CLEARED' if c3['cleared'] else 'not cleared'}")
            if m["replicate"]:
                r = m["replicate"]
                tag = "consistent" if r["consistent"] else "INCONSISTENT — stop and look"
                print(f"  sf replicate check (1.0 vs 0.6): {r['d']:+.0%} "
                      f"[{r['lo']:+.1%}, {r['hi']:+.1%}] — {tag}")
            print()
        print(f"v1 claim-2 verdict: {out['claim2_v1']}")
        return 0

    # figures
    out = judge("runs", dict(ROSTER))
    make_knob_figure(out, KNOB_FIGURE_PATH)
    make_emission_figure(out, EMISSION_FIGURE_PATH)
    print(f"wrote {KNOB_FIGURE_PATH} and {EMISSION_FIGURE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
