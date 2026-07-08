# M4 paper-number extraction — arXiv 2606.25449 v2, logic table (fetched 2026-07-08)

The free extraction task from `docs/M4-BRIEF.md` rider (a): pin the paper-committed
logic wall numbers, verbatim, before any judging. Fetched from the arXiv v2 HTML
(`https://arxiv.org/html/2606.25449v2`) in two independent passes, mirroring the M3
protocol (`evidence/m3/paper-extraction.md`): a targeted llama-wall-cells pass and a
verbatim whole-table character-by-character pass. **The passes agree on every cell**
(values and bracketed CIs) for the llama wall region, which is the only region any M4
artifact consumes.

## tab — the paper's Table 6 (whole-table pass, verbatim)

Caption, verbatim: *"Table 6: Constraint logic: the same three policies, two models.
Directed RR (95% CI) vs. memory integrity g (llama n=96; grok n=24)."*

| g | llama lossy | llama lossy-padded | llama source-first | grok lossy | grok lossy-padded | grok source-first |
|---|---|---|---|---|---|---|
| 1.0 | 0.52 [.43,.61] | 0.36 [.27,.46] | 0.46 [.36,.56] | 0.71 [.50,.88] | 0.96 [.88,1] | 0.75 [.58,.92] |
| 0.6 | 0.40 [.30,.50] | 0.38 [.28,.48] | 0.50 [.40,.59] | 0.92 [.79,1] | 1.00 [1,1] | 0.83 [.67,.96] |
| 0.3 | 0.16 [.08,.23] | 0.18 [.10,.26] | 0.76 [.68,.84] | 0.42 [.21,.62] | 0.38 [.21,.58] | 0.92 [.79,1] |
| 0.1 | 0.05 [.01,.10] | 0.09 [.04,.16] | 0.79 [.71,.86] | 0.50 [.29,.71] | 0.50 [.29,.71] | 0.96 [.88,1] |

The wall cells pinned as `m4.PAPER` (llama·logic, g = 0.3 / 0.1):
lossy **0.16 / 0.05** · lossy_padded **0.18 / 0.09** · source_first **0.76 / 0.79**.

## Cross-validation of the fetch

- The two passes agree cell-for-cell on every llama wall cell, including the CIs.
- The whole-table pass's **grok row matches the author's README wall table exactly**
  (0.42/0.50 · 0.38/0.50 · 0.92/0.96) — the fetch reproduces a row we can verify
  locally, so the extraction is reading a real table, not confabulating one.
- CI widths are internally consistent with the caption's n (llama n=96 intervals
  visibly tighter than grok n=24).

## The README-vs-paper variance (footnote for the M4 close-out)

The author's local README (`~/Projects/reclaim-eval/README.md`, "Directed-arm reclaim
at the wall region") prints the **llama·logic** row as lossy **0.25/0.12**, padded
**0.25/0.04**, source_first **0.67/0.67** — while the paper v2 prints **0.16/0.05**,
**0.18/0.09**, **0.76/0.79**. That is a divergence on **every llama·logic wall cell**,
larger than the last-digit variance M3 found on the arithmetic row (README sf
0.96/1.00 vs paper 0.99/0.99). The pattern is the same, though: the llama rows are
exactly where the v2 parser fix (`NOTE_parser_fix.md`) moved numbers, and the grok row
is untouched. Both sets are the author's numbers; per rider (a) the comparison target
is the **paper's committed values**, and this variance is recorded here and carried
as a footnote wherever the anchor is quoted.

Two things the variance does NOT touch:

- **No gate consumes these numbers** (KICKOFF non-goal: direction + structure, never
  point-matching). D25's gates are the gap, the separation, and the mirrored-ceiling
  shape read — all functions of OUR cells only.
- **The soft-wall shape is the same in both sets**: the lossy floor sits above ~0
  (0.05–0.25 across the two sources), source_first sits well below 1 (0.67–0.79), and
  the gap is decisively positive. If anything the paper's values WIDEN the expected
  gap (sf−lossy ≈ +0.60/+0.74 vs the README's +0.42/+0.55), so the M4 brief's power
  arithmetic (computed on the README anchor) is conservative.

## Sampling note

The M3 extraction (same paper, arithmetic table) records the paper's wall tables as
**temperature 0.7**, three seeds, while our D10 sampling is temperature 0.0 matching
the released tool's default. That labeling carries over: the PAPER column is 0.7,
ours is 0.0 — another reason the anchor is a direction/structure target, not a
point target.
