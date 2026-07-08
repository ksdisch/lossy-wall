"""bootstrap.py — D21's robustness appendix: the paper's bootstrap intervals beside the
Wilson/Newcombe intervals that decided every gate. Wilson decides (D4); this exists so a
reader can check the interval-method choice never drove a verdict.

A **percentile bootstrap** builds an interval by *resampling*: redraw the observed trials
with replacement B times, recompute the rate each time, sort those B rates, and read the
2.5th/97.5th percentiles as the 95% interval. It is distribution-free — but **degenerate**
at extreme cells: every resample of 0/40 is 0/40, so the interval collapses to
[0.000, 0.000], false certainty exactly where the data are most extreme. Our wall cells
LIVE there, which is why D4 made Wilson the decider; the appendix shows the collapse as a
taught result rather than hiding it.

`boot_ci` is the author's own method **re-typed with attribution** (D6's rule: read their
code as reference, re-type, never import — D1's wall): it appears identically in
reclaim-eval's `scripts/analyze_realworld.py` and `scripts/integrity_table_ci.py` —
percentile bootstrap, B=5,000 resamples drawn from `random.Random(seed=0)`, sorted
resample means read at indices int(0.025·B) and int(0.975·B), empty cell → NaN triple.
`boot_ci_diff` applies the same machinery to a difference: each iteration redraws BOTH
arms independently (our arms are treated unpaired everywhere — D5/D14's conservative
convention), d = mech − base in stats.py's orientation.

The appendix covers EXACTLY the numbers that decided verdicts (D21-A) — per model × wall
g: the lossy cell (D14's 0.10 ceiling), its source_first / lossy_padded companions, the
wall gap (sf − lossy), the equivalence gap (padded − lossy, ±δ containment, D7) and the
separation gap (sf − padded); plus deepseek's claim-3 emission cells and gap. 39 rows on
the real roster; the knob descriptives gate nothing and get no rows (D21-C declined). Any
row whose gate property differs between the two methods is flagged DISAGREE and Wilson
stands (D4).

Run ($0, reads only the committed archive):
    uv run bootstrap.py appendix          # the full table over evidence/m1 + evidence/m2
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from grader import EMIT_ATTRACTOR, EMIT_OTHER
from m1 import CEILING, ROSTER, _read_jsonl
from m2 import BLANK_G, BLANK_MODELS, DELTA
from stats import excludes_zero, newcombe_diff, wilson

GATED_G = (0.1, 0.3)     # the wall integrities every claim was judged at (D14/D16)
B = 5000                 # their resample count, verbatim


def boot_ci(xs, n=5000, seed=0):
    """Mean and percentile bootstrap 95% CI of a 0/1 list — the author's `boot_ci`,
    re-typed verbatim from reclaim-eval scripts/analyze_realworld.py (identical copy in
    scripts/integrity_table_ci.py)."""
    if not xs:
        return float("nan"), float("nan"), float("nan")
    r = random.Random(seed)
    k = len(xs)
    means = []
    for _ in range(n):
        means.append(sum(xs[r.randrange(k)] for _ in range(k)) / k)
    means.sort()
    return sum(xs) / k, means[int(0.025 * n)], means[int(0.975 * n)]


def boot_ci_diff(xs_base, xs_mech, n=5000, seed=0):
    """(d, lo, hi) for d = rate(mech) − rate(base), their percentile machinery applied to
    two arms: one `random.Random(seed)` stream, each iteration redrawing base then mech
    INDEPENDENTLY (arms unpaired — D5/D14's conservative convention), sorted diffs read at
    the same int(0.025·n)/int(0.975·n) indices. Either arm empty → NaN triple."""
    if not xs_base or not xs_mech:
        return float("nan"), float("nan"), float("nan")
    r = random.Random(seed)
    kb, km = len(xs_base), len(xs_mech)
    ds = []
    for _ in range(n):
        pb = sum(xs_base[r.randrange(kb)] for _ in range(kb)) / kb
        pm = sum(xs_mech[r.randrange(km)] for _ in range(km)) / km
        ds.append(pm - pb)
    ds.sort()
    return (sum(xs_mech) / km - sum(xs_base) / kb,
            ds[int(0.025 * n)], ds[int(0.975 * n)])


# ── the archived record → 0/1 lists (file order; the committed archive is the input) ──

def _reclaim_lists(root: Path, prefix: str, key: str) -> dict[tuple[str, float], list[int]]:
    rows = _read_jsonl(Path(root) / f"{prefix}-grid-{key}" / "results.jsonl")
    out: dict[tuple[str, float], list[int]] = {}
    for r in rows:
        out.setdefault((r["policy"], r["g"]), []).append(1 if r["reclaimed"] else 0)
    return out


def _emission_list(rows_xs: list[dict]) -> list[int]:
    """Wrong-emission 0/1 per logged row — D17's counting rule applied to the outcome
    string (wrong iff emit_attractor / emit_other_wrong)."""
    return [1 if r["outcome"] in (EMIT_ATTRACTOR, EMIT_OTHER) else 0 for r in rows_xs]


# ── gate properties under an interval (Wilson's and the bootstrap's, same rule) ──────

def _gate_pass(gate: str | None, lo: float, hi: float) -> bool | None:
    if gate is None:
        return None
    if gate == "ceiling":
        return hi <= CEILING
    if gate == "excludes_zero":
        return excludes_zero(lo, hi)
    if gate == "contained":
        return -DELTA < lo and hi < DELTA
    raise ValueError(f"unknown gate {gate!r}")


def _cell_row(claim: int, model: str, label: str, xs: list[int],
              gate: str | None, b: int) -> dict:
    k, n = sum(xs), len(xs)
    w_lo, w_hi = wilson(k, n)
    bm, b_lo, b_hi = boot_ci(xs, n=b)
    wp, bp = _gate_pass(gate, w_lo, w_hi), _gate_pass(gate, b_lo, b_hi)
    return {"claim": claim, "model": model, "kind": "cell", "label": label,
            "k": k, "n": n, "wilson": (w_lo, w_hi), "boot": (bm, b_lo, b_hi),
            "gate": gate, "wilson_pass": wp, "boot_pass": bp,
            "disagree": None if gate is None else wp != bp}


def _gap_row(claim: int, model: str, label: str, xs_base: list[int],
             xs_mech: list[int], gate: str, b: int) -> dict:
    kb, nb = sum(xs_base), len(xs_base)
    km, nm = sum(xs_mech), len(xs_mech)
    d, n_lo, n_hi = newcombe_diff(kb, nb, km, nm)
    bd, b_lo, b_hi = boot_ci_diff(xs_base, xs_mech, n=b)
    wp, bp = _gate_pass(gate, n_lo, n_hi), _gate_pass(gate, b_lo, b_hi)
    return {"claim": claim, "model": model, "kind": "gap", "label": label,
            "k_base": kb, "n_base": nb, "k_mech": km, "n_mech": nm,
            "newcombe": (d, n_lo, n_hi), "boot": (bd, b_lo, b_hi),
            "gate": gate, "wilson_pass": wp, "boot_pass": bp, "disagree": wp != bp}


def appendix(evidence_m1="evidence/m1", evidence_m2="evidence/m2",
             models: dict[str, str] = ROSTER,
             blank_models: tuple[str, ...] = BLANK_MODELS, b: int = B) -> list[dict]:
    """The D21-A rows, recounted from the committed archive: every gated cell rate and
    gap in claims 1–3, each carrying both methods' intervals and its gate verdicts."""
    rows: list[dict] = []
    for key in models:
        c1 = _reclaim_lists(evidence_m1, "m1", key)
        c2 = _reclaim_lists(evidence_m2, "m2", key)
        for g in GATED_G:
            lossy, sf = c1[("lossy", g)], c1[("source_first", g)]
            pad = c2[("lossy_padded", g)]
            rows.append(_cell_row(1, key, f"lossy@{g:g}", lossy, "ceiling", b))
            rows.append(_cell_row(1, key, f"source_first@{g:g}", sf, None, b))
            rows.append(_gap_row(1, key, f"gap sf−lossy @{g:g}", lossy, sf,
                                 "excludes_zero", b))
            rows.append(_cell_row(2, key, f"lossy_padded@{g:g}", pad, None, b))
            rows.append(_gap_row(2, key, f"equivalence padded−lossy @{g:g}", lossy, pad,
                                 "contained", b))
            rows.append(_gap_row(2, key, f"separation sf−padded @{g:g}", pad, sf,
                                 "excludes_zero", b))
    for key in models:
        if key not in blank_models:
            continue
        m1_rows = _read_jsonl(Path(evidence_m1) / f"m1-grid-{key}" / "results.jsonl")
        m2_rows = _read_jsonl(Path(evidence_m2) / f"m2-grid-{key}" / "results.jsonl")
        lossy_emit = _emission_list([r for r in m1_rows
                                     if r["policy"] == "lossy" and r["g"] == BLANK_G])
        blank_emit = _emission_list([r for r in m2_rows if r["policy"] == "blank"])
        rows.append(_cell_row(3, key, "wrong-emission lossy@0.1", lossy_emit, None, b))
        rows.append(_cell_row(3, key, "wrong-emission blank", blank_emit, None, b))
        rows.append(_gap_row(3, key, "emission gap lossy−blank", blank_emit, lossy_emit,
                             "excludes_zero", b))
    return rows


def format_appendix(rows: list[dict]) -> str:
    """The printable appendix: one line per gated number, Wilson/Newcombe beside the
    paper's bootstrap, gate verdicts under both, DISAGREE where they differ."""
    out = ["D21 robustness appendix — Wilson/Newcombe (decided the gates) beside the",
           "author's percentile bootstrap (B=5,000, seed 0, re-typed with attribution).",
           "Wilson decides (D4): on any DISAGREE row the Wilson column is the verdict;",
           "a bootstrap interval of [0.000, 0.000] is the 0/n degeneracy, not certainty.",
           ""]
    hdr = (f"  {'claim':>5} {'model':<9} {'number':<30} {'counts':>12} "
           f"{'Wilson/Newcombe 95%':>24} {'bootstrap 95%':>24} {'gate':<14} {'flag':<8}")
    out += [hdr, "  " + "─" * (len(hdr) - 2)]
    for r in rows:
        if r["kind"] == "cell":
            counts = f"{r['k']}/{r['n']}"
            lo, hi = r["wilson"]
            w = f"[{lo:+.3f}, {hi:+.3f}]"
            bm, blo, bhi = r["boot"]
            btxt = f"[{blo:+.3f}, {bhi:+.3f}]"
        else:
            counts = f"{r['k_mech']}/{r['n_mech']}−{r['k_base']}/{r['n_base']}"
            d, lo, hi = r["newcombe"]
            w = f"{d:+.2f} [{lo:+.3f}, {hi:+.3f}]"
            bd, blo, bhi = r["boot"]
            btxt = f"{bd:+.2f} [{blo:+.3f}, {bhi:+.3f}]"
        gate = r["gate"] or "—"
        if r["gate"] is None:
            flag = ""
        elif r["disagree"]:
            flag = "DISAGREE"
        else:
            flag = "agree"
        out.append(f"  {r['claim']:>5} {r['model']:<9} {r['label']:<30} {counts:>12} "
                   f"{w:>24} {btxt:>24} {gate:<14} {flag:<8}")
    n_dis = sum(1 for r in rows if r["disagree"])
    out += ["", f"  rows: {len(rows)}   gate disagreements: {n_dis}"
            + ("   (Wilson stands on each — D4)" if n_dis else "")]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] != "appendix":
        print(__doc__)
        return 2
    print(format_appendix(appendix()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
