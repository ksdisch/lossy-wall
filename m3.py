"""m3.py — the cross-check + capstone machinery (recount → spotcheck → judge → table →
capstone), D19–D22 in code. M3 measures NOTHING new on our harness: every cell of ours is
an archived, judged-once record under `evidence/`; the only paid trials run through the
author's own released harness (the **oracle run** — "oracle" because we treat its protocol
as the reference to compare against, not because it is infallible: its two known defects
are part of the report). D1's wall stays physical — their code runs only in their clone
under their venv; this module only READS the data files their runner writes.

What each piece is, in plain terms:

  the reader + recount — their `run_pilot.py --fix` checkpoints one JSONL row per
      (seed, problem, policy, integrity, arm) to `data/results/fix_*.jsonl`, carrying the
      parsed answer and their correct flag (not the raw reply, not the temperature — the
      console log is the config record). The recount re-tallies every cell from those rows
      so the M3 checkpoint can compare our count against their console table.
  the spot-check — their score rule re-typed (numeric: parsed answer within 0.5 of the
      problem's truth — their `experiment.py::score`), applied to ≥3 sampled rows per
      policy against the problems' known truth/drift values (dumped from their clone as
      data): logged answer, correct flag, and fixed problem must tell one coherent story.
  the agreement judge (D20) — the pre-committed criterion: per gated overlap cell
      (llama · directed · {lossy, lossy_padded, source_first} × g ∈ {0.1, 0.3}), the
      Newcombe 95% interval on (their rate − our archived rate); AGREE iff all six contain
      zero, else DISCREPANT naming the cell(s) — which triggers the pre-committed audit
      (protocol diff first, readout recount second, cause or "unexplained" reported).
      Judged ONCE, only at the full paper economy (n=96/cell, D19-A) — `judge_ready`
      refuses the seed-1 smoke stage, whose powers are recount-and-eyes only.
  the comparison table (D20) — paper-committed · their-harness-run · ours, every column
      labeled (method / n / temperature / problem economy / arm), the two protocol
      findings and the parser-fixture result as footnotes, claim-3 rows with their
      honesty labels, and the D20 rider-a recount (the archived llama/qwen72b lossy@0.1
      wrong-emission splits, counted once, at table time — a same-protocol neighbor for
      their tab:blank values).
  the capstone (D22) — one self-contained figure: the knob curves per model, claim 3's
      emission bars, and the cross-check panel (ours vs their-run vs paper-committed on
      the llama wall cells). The milestone figures stay frozen as committed records.

Run ($0 unless noted — the oracle run itself happens in THEIR clone, not here):
    uv run m3.py recount   [ckpt]           # re-tally their checkpoint vs their console
    uv run m3.py spotcheck [ckpt] [truths]  # their score rule vs their logged pairs
    uv run m3.py judge     [ckpt]           # the agreement verdict (full economy only)
    uv run m3.py table     [ckpt]           # the labeled comparison table (markdown-ish)
    uv run m3.py capstone  [ckpt]           # docs/figs/capstone.png
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from bootstrap import B, GATED_G, _reclaim_lists, boot_ci
from grader import EMIT_ATTRACTOR, EMIT_OTHER
from m0 import TEMPERATURE
from m1 import _cell_key, _read_jsonl
from m2 import BLANK_G, emission_split
from stats import excludes_zero, newcombe_diff, wilson

OUR_TEMP = TEMPERATURE          # D10 = their tool default; the run's console log confirms

N_ORACLE = 96                   # the paper economy: 32 problems × 3 seeds (D19-A)
WALL_POLICIES = ("lossy", "lossy_padded", "source_first")
GATED_CELLS = tuple((p, g) for p in WALL_POLICIES for g in GATED_G)
KNOB_ORDER = (1.0, 0.6, 0.3, 0.1)

DEFAULT_ORACLE_CKPT = Path(
    "~/Projects/reclaim-eval/data/results/"
    "fix_meta-llama_llama-3.1-8b-instruct_arith.jsonl").expanduser()
DEFAULT_TRUTHS = Path("evidence/m3/their-problems-arith.json")
FIXTURE_OUT = Path("evidence/m3/fixture-parse-answer.txt")
CAPSTONE_PATH = Path("docs/figs/capstone.png")

# The paper's committed numbers, re-typed from the author's artifacts with citations —
# the free extraction task confirms each against the arXiv v2 HTML before the table
# ships (and adds the paper's bootstrap CI brackets + stated sampling config there).
PAPER = {
    # README "Findings" table, row "llama-3.1-8b · arithmetic", directed arm, shown as
    # g=0.3 / g=0.1; n=96 per their scripts/integrity_table_ci.py (32 problems × 3 seeds)
    "wall_llama": {("lossy", 0.3): 0.00, ("lossy", 0.1): 0.00,
                   ("lossy_padded", 0.3): 0.00, ("lossy_padded", 0.1): 0.00,
                   ("source_first", 0.3): 0.96, ("source_first", 0.1): 1.00},
    "wall_n": 96,
    # NOTE_parser_fix.md, post-v2 corrected disposition deltas (n=96/cell, g=0.1,
    # directed); "frontier" = the four OpenAI/Anthropic abstainers, all 0.00
    "disposition_delta": {"deepseek-chat": 0.83, "qwen-2.5-7b": 0.39,
                          "llama-3.1-8b": 0.17, "frontier": 0.00},
    # NOTE_parser_fix.md, tab:blank corrected lossy-emit value for llama
    "blank_lossy_emit_llama": 0.17,
    # their README header: "Core sweep: 8 problems x 3 seeds, temperature 0.7" — their
    # run_pilot tool default is 0.0; the extraction task pins what the PAPER states for
    # tab:wall, and the table's temperature column carries the label either way
    "sweep_temp_readme": 0.7,
}

# Our M0 disposition-probe records (judged verdicts; ROADMAP.md D9/D13 tables):
# (wrong_lossy, n_lossy, wrong_blank, n_blank) at g=0.1, directed, 12/arm
OUR_PROBE = {"llama": (1, 12, 0, 12), "qwen72b": (0, 12, 0, 12)}


# ── their checkpoint: reader, cells, recount ─────────────────────────────────────────

_REQUIRED = ("pid", "integrity", "arm", "policy", "answer", "correct", "seed")


def read_fix_rows(path) -> list[dict]:
    """Their fix_*.jsonl rows, schema-checked: every row must carry the keys their
    runner writes — a missing key means the file is not what the run was supposed to
    produce, and the recount must fail loudly, not tally garbage."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        missing = [k for k in _REQUIRED if k not in r]
        if missing:
            raise ValueError(f"their row is missing {missing} — not a fix_*.jsonl row: "
                             f"{r}")
        rows.append(r)
    return rows


def oracle_cells(rows: list[dict], arm: str = "directed") -> dict[tuple[str, float], list[int]]:
    """One arm's 0/1 outcome lists per (policy, integrity), file order — the recount's
    substrate, and the judge's their-side input (directed is the gated arm, D2; the
    generic rows ride along as reference only)."""
    out: dict[tuple[str, float], list[int]] = {}
    for r in rows:
        if r["arm"] != arm:
            continue
        out.setdefault((r["policy"], r["integrity"]), []).append(1 if r["correct"] else 0)
    return out


def recount(rows: list[dict]) -> dict:
    """Every cell re-tallied from their rows (both arms), with the unit bookkeeping
    that makes completeness mechanical: their runner writes one full integrity×arm
    block per (seed, pid, policy) unit, so a complete file has every cell's n equal to
    pids × seeds."""
    cells: dict[tuple[str, float, str], dict] = {}
    pids, seeds, units = set(), set(), set()
    for r in rows:
        pids.add(r["pid"])
        seeds.add(r["seed"])
        units.add((r["seed"], r["pid"], r["policy"]))
        c = cells.setdefault((r["policy"], r["integrity"], r["arm"]),
                             {"k": 0, "n": 0})
        c["n"] += 1
        c["k"] += 1 if r["correct"] else 0
    for c in cells.values():
        c["rate"] = c["k"] / c["n"] if c["n"] else float("nan")
    expected = len(pids) * len(seeds)
    return {"cells": cells, "pids": len(pids), "seeds": sorted(seeds),
            "units": len(units),
            "complete": bool(cells) and all(c["n"] == expected for c in cells.values())}


# ── the agreement judge (D20's criterion, pre-committed) ─────────────────────────────

def agreement_judge(theirs: dict[tuple[str, float], tuple[int, int]],
                    ours: dict[tuple[str, float], tuple[int, int]]) -> dict:
    """The pre-committed criterion over the six gated overlap cells: the Newcombe 95%
    interval on d = (their rate − our archived rate), unequal n as always. AGREE iff
    every interval contains zero; any exclusion → DISCREPANT naming the cell(s), which
    hands off to the pre-committed audit (protocol diff first, recount second). Pure
    function of the two count tables — the verdict rule existed before the data."""
    cells: dict[tuple[str, float], dict] = {}
    discrepant: list[str] = []
    for cell in GATED_CELLS:
        ko, no = ours[cell]
        kt, nt = theirs[cell]
        d, lo, hi = newcombe_diff(ko, no, kt, nt)     # base=ours, mech=theirs
        consistent = not excludes_zero(lo, hi)
        cells[cell] = {"ours": (ko, no), "theirs": (kt, nt),
                       "d": d, "lo": lo, "hi": hi, "consistent": consistent}
        if not consistent:
            discrepant.append(_cell_key(*cell))
    return {"cells": cells, "discrepant": discrepant,
            "verdict": "AGREE" if not discrepant else "DISCREPANT"}


def judge_ready(theirs_lists: dict[tuple[str, float], list[int]],
                n_full: int = N_ORACLE) -> bool:
    """Judged once, at the full paper economy only: every gated cell present at
    n ≥ 96. The seed-1 smoke stage (n=32) must never reach the judge — its checkpoint
    powers are recount, eyes, and cost confirmation (the brief, verbatim)."""
    return all(len(theirs_lists.get(cell, [])) >= n_full for cell in GATED_CELLS)


# ── our archived record (the judged-once comparators) ────────────────────────────────

def our_cells(key: str, evidence_m1="evidence/m1",
              evidence_m2="evidence/m2") -> dict[tuple[str, float], tuple[int, int]]:
    """One model's archived cells, merged m1+m2 grids, as (k, n) — recounted from the
    committed evidence, never from memory (the numbers are judged records; the recount
    is just wiring)."""
    lists = _reclaim_lists(evidence_m1, "m1", key)
    lists.update(_reclaim_lists(evidence_m2, "m2", key))
    return {cell: (sum(xs), len(xs)) for cell, xs in lists.items()}


# ── the spot-check (their score rule, re-typed, vs their logged pairs) ───────────────

def spot_check(rows: list[dict], truths: dict[str, dict], k: int = 3,
               rng_seed: int = 0) -> dict:
    """≥k sampled rows per policy, each checked for internal consistency: their logged
    `correct` flag must equal what their own score rule says about their logged
    `answer` (numeric: within 0.5 of the problem's truth — their experiment.py::score,
    re-typed). `is_attractor` marks a wrong answer that equals the planted drift value
    (the inherited stale number, the failure mode the whole project measures)."""
    records = []
    consistent_all = True
    for policy in WALL_POLICIES:
        pool = [r for r in rows if r["policy"] == policy]
        rng = random.Random(f"{rng_seed}-{policy}")
        for r in rng.sample(pool, min(k, len(pool))):
            t = truths[r["pid"]]
            ans = r["answer"]
            expected = ans is not None and abs(ans - t["correct"]) < 0.5
            consistent = expected == bool(r["correct"])
            rec = {"pid": r["pid"], "policy": policy, "arm": r["arm"],
                   "integrity": r["integrity"], "answer": ans,
                   "correct": bool(r["correct"]), "expected_correct": expected,
                   "consistent": consistent,
                   "is_attractor": ans is not None and abs(ans - t["drift"]) < 0.5}
            records.append(rec)
            consistent_all = consistent_all and consistent
    return {"records": records, "all_consistent": consistent_all}


# ── the D20 rider-a recount (counted once, at table time, gating nothing) ────────────

def rider_a_recount(evidence_m1="evidence/m1",
                    models: tuple[str, ...] = ("llama", "qwen72b")) -> dict[str, dict]:
    """The pre-declared descriptive recount: the ARCHIVED llama and qwen72b lossy@0.1
    rows' abstain-vs-emit split (n=40 each), so their tab:blank lossy-emit values get a
    same-protocol neighbor in the table. Extends nothing D17 declined: no new trials,
    no gate, the blank arms stay at probe n=12."""
    out = {}
    for key in models:
        rows = _read_jsonl(Path(evidence_m1) / f"m1-grid-{key}" / "results.jsonl")
        out[key] = emission_split([r for r in rows
                                   if r["policy"] == "lossy" and r["g"] == BLANK_G])
    return out


# ── the comparison table (D20: every column labeled, every finding footnoted) ────────

def _cell_text(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.2f} W[{lo:.2f}, {hi:.2f}]"


def comparison_table(theirs: dict[tuple[str, float], list[int]],
                     fixture_line: str | None = None,
                     evidence_m1="evidence/m1", evidence_m2="evidence/m2",
                     b: int = B) -> str:
    """The paper-comparison table: paper-committed · their-harness-run · ours per
    overlap cell (gated wall cells + descriptive knob cells), then the claim-3 rows
    with their honesty labels, then the label legend and the protocol-finding
    footnotes. Markdown-ish text, ready for ROADMAP.md and the README's short form."""
    ours = our_cells("llama", evidence_m1, evidence_m2)
    out = ["## The comparison table — llama · arithmetic · directed",
           "",
           "| cell | tier | paper-committed | their-harness-run | ours |",
           "|---|---|---|---|---|"]
    gs = [g for g in KNOB_ORDER if any((p, g) in theirs for p in WALL_POLICIES)]
    for g in gs:
        for policy in WALL_POLICIES:
            if (policy, g) not in theirs:
                continue
            tier = "gated" if g in GATED_G else "descriptive"
            paper = PAPER["wall_llama"].get((policy, g))
            p_txt = f"{paper:.2f} (n={PAPER['wall_n']})" if paper is not None else "—"
            xs = theirs[(policy, g)]
            _, blo, bhi = boot_ci(xs, n=b)
            t_txt = (f"{_cell_text(sum(xs), len(xs))} B[{blo:.2f}, {bhi:.2f}]")
            o = ours.get((policy, g))
            o_txt = _cell_text(*o) if o else "—"
            out.append(f"| {_cell_key(policy, g)} | {tier} | {p_txt} | {t_txt} | {o_txt} |")
    out += [
        "",
        "column labels (method / n / temperature / problem economy / arm):",
        "- **paper-committed** — their bootstrap CI (B=5,000; brackets from the arXiv "
        f"v2 extraction), n={PAPER['wall_n']} (32 fixed problems × 3 seeds), "
        f"temperature: their README header says the core sweep ran "
        f"{PAPER['sweep_temp_readme']:g} (the extraction pins what the paper states "
        "for tab:wall); their problem economy (session 1 rebuilt per policy); "
        "directed arm.",
        f"- **their-harness-run** — our recount of their fix_*.jsonl rows; Wilson (W) "
        f"and their own boot_ci (B) both computed from the same rows; their tool "
        f"defaults (temperature {OUR_TEMP:g} = our D10), their problem economy, "
        "directed arm.",
        f"- **ours** — archived judged-once cells (evidence/), Wilson, n=40–90, "
        f"temperature {OUR_TEMP:g}, fresh problem per trial (D5), directed arm.",
        "",
        "### Claim 3 beside their disposition table (labels carried per row)",
        ""]
    # deepseek: our judged gap vs their delta
    ds_m1 = _read_jsonl(Path(evidence_m1) / "m1-grid-deepseek" / "results.jsonl")
    ds_m2 = _read_jsonl(Path(evidence_m2) / "m2-grid-deepseek" / "results.jsonl")
    l_split = emission_split([r for r in ds_m1
                              if r["policy"] == "lossy" and r["g"] == BLANK_G])
    b_split = emission_split([r for r in ds_m2 if r["policy"] == "blank"])
    d, lo, hi = newcombe_diff(b_split["wrong"], b_split["n"],
                              l_split["wrong"], l_split["n"])
    out.append(
        f"- **deepseek** — ours: wrong-emission gap {d:+.0%} [{lo:+.1%}, {hi:+.1%}] "
        f"(lossy {l_split['wrong']}/{l_split['n']} vs blank {b_split['wrong']}/"
        f"{b_split['n']}, fresh problems, temp {OUR_TEMP:g}, arms sampled on "
        f"different dates as pre-registered) · theirs: Δ+"
        f"{PAPER['disposition_delta']['deepseek-chat']:.2f} (n={PAPER['wall_n']}, "
        "their problems, their sweep config).")
    # llama: our probe NULL, concordant with their small delta
    wl, nl, wb, nb = OUR_PROBE["llama"]
    d, lo, hi = newcombe_diff(wb, nb, wl, nl)
    out.append(
        f"- **llama** — ours: probe NULL {wl}/{nl} vs {wb}/{nb} ({d:+.0%} "
        f"[{lo:+.0%}, {hi:+.0%}], n=12/arm, underpowered by pre-commitment — D17 "
        f"rider a declined) · theirs: Δ+{PAPER['disposition_delta']['llama-3.1-8b']:.2f} "
        "— our probe interval already contains their value.")
    out.append(
        f"- **qwen** — theirs: qwen-2.5-7b Δ+"
        f"{PAPER['disposition_delta']['qwen-2.5-7b']:.2f} — **no comparable cell**: "
        "our slot ran qwen-2.5-72b-instruct, a same-family 10×-size substitute "
        "(D13's standing label), never presented as the paper's model. Our 72b probe: "
        f"{OUR_PROBE['qwen72b'][0]}/12 vs {OUR_PROBE['qwen72b'][2]}/12 (abstainer NULL).")
    # rider a: the archived wrong-emission splits, counted here, at table time
    rider = rider_a_recount(evidence_m1)
    out += ["",
            "### D20 rider-a recount (archived lossy@0.1 wrong-emission splits, "
            "counted once at table time, gating nothing)",
            ""]
    for key, s in rider.items():
        rate = s["wrong"] / s["n"] if s["n"] else 0.0
        wlo, whi = wilson(s["wrong"], s["n"])
        neighbor = (f" · their tab:blank llama lossy-emit "
                    f"{PAPER['blank_lossy_emit_llama']:.2f}" if key == "llama" else "")
        out.append(f"- **{key}** lossy@{BLANK_G:g} wrong-emission {s['wrong']}/{s['n']} "
                   f"= {rate:.2f} W[{wlo:.2f}, {whi:.2f}] (attractor {s['attractor']}, "
                   f"other {s['other_wrong']}, abstain {s['abstain']}, reclaimed "
                   f"{s['reclaimed']}){neighbor}")
    out += [
        "",
        "footnotes — the protocol findings:",
        "1. their `reproduce_tables.py` exits nonzero on the public repo (it ships an "
        "empty data/results/ directory) — the \"every table reproduces from committed "
        "results\" claim fails on the artifact as shipped (M0 finding, reconfirmed in "
        "M3).",
        "2. their `parse_answer` wrap set has no backslash escape, so `ANSWER: \\$197` "
        "reads as an abstention — their deepseek/qwen cells may under-read escaped "
        "commits as abstentions. An under-read on the lossy arm can only SHRINK a "
        "lossy−blank emission gap, so their deepseek Δ+0.83 would be a floor, not an "
        f"artifact, if it bit at all. {fixture_line or 'fixture check: pending'}.",
        "3. whether it moved their published numbers is unknowable from their "
        "committed artifacts (no raw replies in their rows).",
    ]
    return "\n".join(out)


# ── the capstone (D22: one self-contained figure) ────────────────────────────────────

def make_capstone(ours_by_model: dict[str, dict[tuple[str, float], tuple[int, int]]],
                  emission: dict[str, dict], oracle: dict[tuple[str, float], tuple[int, int]],
                  path=CAPSTONE_PATH) -> None:
    """docs/figs/capstone.png — the whole v1 story in one image: the knob curves per
    model (lossy + source_first, padded points and the blank point at the wall), the
    claim-3 emission bars, and the cross-check panel (ours vs their-run vs
    paper-committed on the six llama wall cells). Milestone figures stay frozen."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_models = len(ours_by_model)
    fig = plt.figure(figsize=(5.0 * max(3, n_models), 8.6))
    gs = fig.add_gridspec(2, max(3, n_models), height_ratios=(1.0, 1.0))

    knob_axis = (0.1, 0.3, 0.6, 1.0)
    for i, (key, cells) in enumerate(ours_by_model.items()):
        ax = fig.add_subplot(gs[0, i])
        for policy, color, marker in (("lossy", "#c0392b", "o"),
                                      ("source_first", "#2471a3", "s"),
                                      ("lossy_padded", "#e67e22", "D")):
            xs, ys, lo_e, hi_e = [], [], [], []
            for g in knob_axis:
                if (policy, g) not in cells:
                    continue
                k, n = cells[(policy, g)]
                rate = k / n
                lo, hi = wilson(k, n)
                xs.append(g)
                ys.append(rate)
                lo_e.append(rate - lo)
                hi_e.append(hi - rate)
            if not xs:
                continue
            style = dict(linestyle="none") if policy == "lossy_padded" else {}
            ax.errorbar(xs, ys, yerr=[lo_e, hi_e], color=color, marker=marker,
                        capsize=3, label=policy, **style)
        if ("blank", BLANK_G) in cells:
            k, n = cells[("blank", BLANK_G)]
            rate = k / n
            lo, hi = wilson(k, n)
            ax.errorbar([BLANK_G], [rate], yerr=[[rate - lo], [hi - rate]],
                        color="#27ae60", marker="^", capsize=3, linestyle="none",
                        label="blank")
        ax.set_xticks(knob_axis)
        ax.set_xlim(0.0, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_title(key)
        ax.set_xlabel("note integrity g")
        ax.grid(alpha=0.25)
        if i == 0:
            ax.set_ylabel("reclaim rate (directed)")
            ax.legend(loc="center right", fontsize=8)

    # claim 3's picture: the emission bars (the roster's emitter)
    ax = fig.add_subplot(gs[1, 0])
    for x, (arm, color) in enumerate((("lossy", "#c0392b"), ("blank", "#7f8c8d"))):
        s = emission[arm]
        rate = s["wrong"] / s["n"] if s["n"] else 0.0
        lo, hi = wilson(s["wrong"], s["n"])
        ax.bar(x, rate, color=color, width=0.6)
        ax.errorbar(x, rate, yerr=[[rate - lo], [hi - rate]], color="black", capsize=5)
        ax.annotate(f"{s['wrong']}/{s['n']}", (x, rate), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"lossy@{BLANK_G:g}", "blank"])
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("wrong-emission rate")
    ax.set_title("worse than empty (deepseek)")
    ax.grid(alpha=0.25, axis="y")

    # the cross-check panel: ours vs their-run vs paper on the six llama wall cells
    ax = fig.add_subplot(gs[1, 1:])
    labels, xpos = [], []
    for j, (policy, g) in enumerate(GATED_CELLS):
        xpos.append(j)
        labels.append(f"{policy}\n@{g:g}")
        series = (("ours", ours_by_model.get("llama", {}).get((policy, g)),
                   "#2471a3", -0.22),
                  ("their run", oracle.get((policy, g)), "#8e44ad", 0.0),
                  ("paper", None, "#16a085", 0.22))
        for name, kn, color, dx in series:
            if name == "paper":
                v = PAPER["wall_llama"].get((policy, g))
                if v is not None:
                    ax.plot(j + dx, v, marker="*", color=color, markersize=10,
                            linestyle="none",
                            label=name if j == 0 else None)
                continue
            if kn is None:
                continue
            k, n = kn
            rate = k / n
            lo, hi = wilson(k, n)
            ax.errorbar(j + dx, rate, yerr=[[rate - lo], [hi - rate]], color=color,
                        marker="o", capsize=3, linestyle="none",
                        label=name if j == 0 else None)
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("the cross-check: two independent builds + the paper (llama, wall)")
    ax.grid(alpha=0.25, axis="y")
    ax.legend(loc="center left", fontsize=8)

    fig.suptitle("lossy-wall v1 — the wall, the control, the title claim, and the "
                 "independent-build check (Wilson 95%; paper points as committed)")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ── CLI ──────────────────────────────────────────────────────────────────────────────

def _load_ckpt(argv: list[str], i: int = 2) -> list[dict]:
    path = Path(argv[i]).expanduser() if len(argv) > i else DEFAULT_ORACLE_CKPT
    if not path.exists():
        raise SystemExit(f"no oracle checkpoint at {path} — the run writes it in "
                         f"their clone (data/results/)")
    return read_fix_rows(path)


def main(argv: list[str]) -> int:
    cmds = ("recount", "spotcheck", "judge", "table", "capstone")
    if len(argv) < 2 or argv[1] not in cmds:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "recount":
        rows = _load_ckpt(argv)
        out = recount(rows)
        print(f"their checkpoint recount — {len(rows)} rows, {out['pids']} problems, "
              f"seeds {out['seeds']}, {out['units']} units "
              f"({'complete' if out['complete'] else 'INCOMPLETE — mid-run or lost rows'})\n")
        for arm in ("directed", "generic"):
            print(f"  {arm} arm{' (reference only — gates nothing, D2)' if arm == 'generic' else ''}:")
            print(f"  {'integrity':>9} {'LOSSY':>16} {'LOSSY_PAD':>16} {'SOURCE_1st':>16}")
            for g in KNOB_ORDER:
                parts = []
                for policy in WALL_POLICIES:
                    c = out["cells"].get((policy, g, arm))
                    parts.append(f"{c['k']:>3}/{c['n']:<3} {c['rate']:.2f}" if c else "—")
                print(f"  {g:>9} {parts[0]:>16} {parts[1]:>16} {parts[2]:>16}")
            print()
        print("  (compare the rates against their console table — they must match at "
              "2 decimals; the counts are the recount of record)")
        return 0

    if cmd == "spotcheck":
        rows = _load_ckpt(argv)
        tpath = Path(argv[3]).expanduser() if len(argv) > 3 else DEFAULT_TRUTHS
        if not tpath.exists():
            raise SystemExit(f"no truths dump at {tpath} — run the dump script in "
                             f"their clone first (free oracle-side checks)")
        truths = json.loads(tpath.read_text(encoding="utf-8"))
        out = spot_check(rows, truths)
        for r in out["records"]:
            tag = "ok" if r["consistent"] else "INCONSISTENT"
            att = " [attractor]" if r["is_attractor"] else ""
            print(f"  {r['policy']:<13} g={r['integrity']:<4} {r['arm']:<8} "
                  f"{r['pid']:<10} answer={r['answer']} correct={r['correct']} "
                  f"expected={r['expected_correct']} -> {tag}{att}")
        print(f"\n  spot-check: {'ALL CONSISTENT' if out['all_consistent'] else 'INCONSISTENT — stop and look'}")
        return 0 if out["all_consistent"] else 1

    if cmd == "judge":
        rows = _load_ckpt(argv)
        lists = oracle_cells(rows)
        if not judge_ready(lists):
            print(f"agreement judge: PENDING — the criterion is judged once, at the "
                  f"full paper economy (n={N_ORACLE}/cell). Current gated-cell counts:")
            for cell in GATED_CELLS:
                print(f"  {_cell_key(*cell):<20} n={len(lists.get(cell, []))}")
            print("  (the seed-1 checkpoint's powers are recount + eyes + cost only)")
            return 1
        theirs = {cell: (sum(lists[cell]), len(lists[cell])) for cell in GATED_CELLS}
        ours = our_cells("llama")
        out = agreement_judge(theirs, ours)
        print("the cross-check agreement criterion (pre-committed in docs/M3-BRIEF.md):\n")
        for cell, c in out["cells"].items():
            ko, no = c["ours"]
            kt, nt = c["theirs"]
            tag = "consistent" if c["consistent"] else "EXCLUDES ZERO"
            print(f"  {_cell_key(*cell):<20} theirs {kt:>3}/{nt:<3} ours {ko:>3}/{no:<3} "
                  f"d={c['d']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}] {tag}")
        print(f"\n  verdict: {out['verdict']}"
              + (f" — discrepant cells: {', '.join(out['discrepant'])}; the "
                 f"pre-committed audit runs (protocol diff first, recount second)"
                 if out["discrepant"] else " — all six intervals contain zero"))
        # their internal wall structure, descriptive only (our comparators already
        # encode the structure; this gates nothing)
        for g in GATED_G:
            sf, lo_ = theirs[("source_first", g)], theirs[("lossy", g)]
            d, lo, hi = newcombe_diff(lo_[0], lo_[1], sf[0], sf[1])
            print(f"  descriptive: their sf−lossy @ g={g:g}: {d:+.0%} "
                  f"[{lo:+.1%}, {hi:+.1%}]")
        return 0

    if cmd == "table":
        rows = _load_ckpt(argv)
        fixture_line = None
        if FIXTURE_OUT.exists():
            for line in FIXTURE_OUT.read_text(encoding="utf-8").splitlines():
                if line.startswith("SUMMARY:"):
                    fixture_line = line.removeprefix("SUMMARY:").strip()
                    break
        print(comparison_table(oracle_cells(rows), fixture_line=fixture_line))
        return 0

    # capstone
    rows = _load_ckpt(argv)
    lists = oracle_cells(rows)
    if not judge_ready(lists):
        raise SystemExit(f"capstone: the oracle run has not reached the full economy "
                         f"(n={N_ORACLE}/cell) — the figure draws the judged record only")
    oracle = {cell: (sum(lists[cell]), len(lists[cell])) for cell in GATED_CELLS}
    ours_by_model = {key: our_cells(key) for key in ("llama", "deepseek", "qwen72b")}
    ds_m1 = _read_jsonl(Path("evidence/m1") / "m1-grid-deepseek" / "results.jsonl")
    ds_m2 = _read_jsonl(Path("evidence/m2") / "m2-grid-deepseek" / "results.jsonl")
    emission = {"lossy": emission_split([r for r in ds_m1 if r["policy"] == "lossy"
                                         and r["g"] == BLANK_G]),
                "blank": emission_split([r for r in ds_m2 if r["policy"] == "blank"])}
    make_capstone(ours_by_model, emission, oracle, CAPSTONE_PATH)
    print(f"wrote {CAPSTONE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
