# Cross-Check-Against-Author-Code

## Purpose
Answers "what did comparing our independent harness against the author's own code reveal,
and what did it prove?" for a reader who wants to understand the protocol-validation
design and its findings. Synthesises across `DECISIONS.md` D1 and D19–D22, `ROADMAP.md`
M3, `LEARNING.md` M3, and the evidence record — no single source tells the complete story.

## Key understanding

### Why an independent build, not a re-run

**Decision** — D1, [`DECISIONS.md`](../DECISIONS.md): build the harness in-repo; use the
author's released harness (`reclaim-eval`, Apache-2.0) as a protocol reference and
cross-check oracle on ONE pre-committed overlapping cell. The author's code is never
imported by the project's harness, never listed in `pyproject.toml`.

**Inference** — this design tests the paper's *description*, not the paper's *code*:
re-running the author's code would only confirm their code runs; rebuilding from the
paper's text and then meeting their code at one cell tests whether the written protocol
is complete enough to reproduce from. That is the project's riskiest assumption #4, from
[`docs/KICKOFF.md`](../docs/KICKOFF.md). Rests on [`LEARNING.md` M3](../LEARNING.md)
("a replication is not a re-run").

### What the oracle run was

**Decision** — D19, [`DECISIONS.md`](../DECISIONS.md): run `run_pilot.py --real --fix
--task arith` on llama-3.1-8b-instruct at the author's tool defaults (temperature 0.0,
the paper's full 32-problems × 3-seeds economy, n=96 per cell). Staged: seed-1 smoke
→ M3 checkpoint → `--seeds 3` resume. Cost: $0.055 measured. Wall-clock: ≈7.6h serial
(provider slow; the brief's 2.5–4.5h estimate was wall-clock only, not cost).

**Fact** — llama was chosen as the oracle model because it is the paper's own primary
model, and the cross-check cell was on the arithmetic family where D6's verbatim note
templates apply. Deepseek was not chosen because their parser carries the escaped-`\$`
blindspot (surfaced in M1), so disagreement there could not separate protocol drift from
their parser bug. Source: [`DECISIONS.md`](../DECISIONS.md) D19.

**Fact** — the oracle run is the only place where the author's harness and this project's
harness share a cell. Their code ran unmodified in its own isolated venv; no shared
code path exists between the two harnesses. Source: [`DECISIONS.md`](../DECISIONS.md) D1.

### The cross-check verdict

**Decision** — D20, [`DECISIONS.md`](../DECISIONS.md): AGREE iff every Newcombe 95%
interval on (their rate − ours) contains zero on all 6 gated wall-region overlap cells.
DISCREPANT triggers a protocol audit. The verdict is a separate protocol-fidelity line,
never compounded into claim verdicts.

**Fact** — verdict: **AGREE — all 6 intervals contain zero**. The comparison numbers
(from [`ROADMAP.md` M3 cross-check table](../ROADMAP.md)):

| cell | theirs (n=96) | ours | interval on (theirs − ours) |
|---|---|---|---|
| lossy@0.1 | 0/96 | 0/40 | [−0.088, +0.038] |
| lossy@0.3 | 1/96 | 0/40 | [−0.078, +0.057] |
| lossy_padded@0.1 | 0/96 | 0/40 | [−0.088, +0.038] |
| lossy_padded@0.3 | 0/96 | 0/40 | [−0.088, +0.038] |
| source_first@0.1 | 96/96 | 40/40 | [−0.038, +0.088] |
| source_first@0.3 | 96/96 | 40/40 | [−0.038, +0.088] |

**Inference** — the near-zero differences (no gap at all on most cells) imply that two
codebases, written independently from the same paper, converged on numerically
indistinguishable results. This is unusually clean for a replication — it rests on D6's
verbatim templates and D10's matched sampling (temperature 0.0). Rests on reading the
table and the D6/D10 design choices together.

### What the oracle run found about the author's code

**Fact** — the M3 free phase (before the oracle run started) ran a parser fixture test:
the author's `parse_answer` has no backslash-escape case, so `ANSWER: \$197` is read as
no-commit. Their parser read 0 of 8 archived escaped ANSWER lines as commits; ours reads
8 of 8. Plain controls agree 4/4. This means their deepseek cells may have
under-read escaped commits as abstentions. Source: [`ROADMAP.md` M3 footnote 2](../ROADMAP.md).

**Inference** — an under-read on their lossy arm can only shrink their lossy-minus-blank
emission gap, so their reported deepseek Δ+0.83 is a floor, not an artifact.
Rests on directional reasoning stated in [`ROADMAP.md` M3 footnote 2](../ROADMAP.md).

**Fact** — the author's `reproduce_tables.py` exits nonzero on the public repo (the
`data/results/` directory is empty); the "every table reproduces from committed results"
claim fails on the artifact as shipped. This was a M0 finding, reconfirmed in M3.
Source: [`ROADMAP.md` M3 footnote 1](../ROADMAP.md).

**Fact** — arXiv v2 and the author's README disagree in the last digit on three wall
cells (paper lossy@0.3 0.01 vs README 0.00; sf 0.99/0.99 vs README 0.96/1.00). The
comparison table carries the paper's values; the variance is footnoted. Source:
[`ROADMAP.md` M3 footnote 4](../ROADMAP.md).

**Fact** — the paper's tab:wall ran at temperature 0.7 (the paper's own caption);
the oracle run used temperature 0.0 (their tool default = this project's D10). The two
runs are sampling-matched to each other but not to the paper's published table. This is
labeled in the comparison table. Source: [`ROADMAP.md` M3 comparison table column labels](../ROADMAP.md).

### The bootstrap appendix: why Wilson decides

**Decision** — D21, [`DECISIONS.md`](../DECISIONS.md): re-type the author's `boot_ci`
verbatim (B=5,000, seed 0, percentile) and run it on every gated cell and gap — the
appendix that lets the comparison table show both methods, labeled.

**Fact** — the appendix produced 39 rows, zero Wilson-vs-bootstrap gate disagreements.
The method choice never drove a verdict. Source: [`ROADMAP.md` M3 D21](../ROADMAP.md).

**Fact** — the degenerate case showed exactly as predicted: every 0/40 cell's bootstrap
collapses to [0.000, 0.000] (maximal confidence from 40 identical zeros resampled 5,000
times); Wilson reports [0%, 8.8%] (honest uncertainty). This is the argument for D4's
choice of Wilson as the decider: false certainty at the extremes is worse than admitting
the evidence only rules out ≥8.8%, not ≥0%. Source: [`LEARNING.md` M3](../LEARNING.md),
[`DECISIONS.md`](../DECISIONS.md) D21 outcome.

### What the AGREE verdict retires

**Inference** — AGREE retires riskiest assumption #4 from [`docs/KICKOFF.md`](../docs/KICKOFF.md):
"our independent build matches the protocol." Two codebases, same paper, same cell,
same answer. The claim verdicts are now independently corroborated at the level of the
protocol — not just internally consistent. Rests on the KICKOFF's framing of this
assumption and the M3 AGREE outcome together.

**Fact** — DISCREPANT would not have changed the claim verdicts (D20 design), but would
have triggered a protocol audit (protocol diff first, readout recount second). This
contingency never fired. Source: [`DECISIONS.md`](../DECISIONS.md) D20.

## Sources
- [`DECISIONS.md`](../DECISIONS.md) — D1 (independent build contract), D19 (oracle run design), D20 (verdict criterion and fidelity-line separation), D21 (bootstrap appendix), D22 (capstone incorporating the cross-check panel)
- [`ROADMAP.md`](../ROADMAP.md) — M3 cross-check verdict table, comparison table, cost ledger, four footnotes on author-code findings
- [`LEARNING.md`](../LEARNING.md) — M3 teaching note ("a replication is not a re-run", degeneracy lesson, bootstrap degeneracy)
- [`docs/KICKOFF.md`](../docs/KICKOFF.md) — riskiest assumption #4, the cross-check stage in the phased plan

## Uncertainties & contradictions

**Unresolved** — whether the author's published table values were affected by their
escaped-dollar parser bug is unknowable from their committed artifacts (no raw replies
in their rows). Reported in [`ROADMAP.md` M3 footnote 3](../ROADMAP.md).

**Contradiction** — the paper and the author's own README disagree on three wall cells
(last-digit discrepancy). Neither value can be confirmed as authoritative from the
available artifacts; the project carries the paper's values with a footnote.

## Related pages
- [Results-Synthesis](Results-Synthesis.md)
- [Methodology-Guardrails](Methodology-Guardrails.md)

## Relevance to current work
This project is CLOSED (D31, 2026-07-09). A future reader would come here to understand
the cross-check design as a reusable protocol — the AGREE verdict structure, the
oracle-cell selection rationale (choose the anchor model, not the model with a
known parser issue), and the bootstrap-appendix pattern for showing a method choice
never drove a verdict. These patterns transferred to the ghost-patch and dim-stage
successor projects.

_Last reviewed: 2026-07-26_
