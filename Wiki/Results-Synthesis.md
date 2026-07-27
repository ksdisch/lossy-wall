# Results-Synthesis

## Purpose
Answers "what did this replication actually measure and find, end to end?" for a reader
who wants the headline numbers and outcomes in one place without reading six milestone
sections. Synthesises across M0–M5 results, cost ledgers, and the pre-registered prediction
vs observed outcome for every claim.

## Key understanding

### Pre-registered claims and verdicts

**Fact** — three claims were pre-registered in `docs/KICKOFF.md` before any paid call:

| Claim | Pre-registered gate | Observed verdict | Source |
|---|---|---|---|
| 1 — the wall | lossy Wilson-95 upper bound ≤ 0.10; Newcombe (sf − lossy) excludes zero; both g ∈ {0.1, 0.3}; ≥2 models | **REPRODUCED — 3/3 models** | `ROADMAP.md` M1 |
| 2 — content, not length | Newcombe (lossy_padded − lossy) contained in ±0.10 AND (sf − lossy_padded) excludes zero; both g; ≥2 models | **REPRODUCED — 3/3 models** | `ROADMAP.md` M2 |
| 3 — worse than empty | Newcombe (wrong-emission lossy − blank) excludes zero; on ≥1 disposed-to-answer model | **REPRODUCED — deepseek only (predicted null on llama, qwen72b)** | `ROADMAP.md` M2 |
| Cross-check | Newcombe (their harness − ours) contains zero on all 6 wall-region overlap cells | **AGREE — 6/6** | `ROADMAP.md` M3 |
| M4 — logic family | gap (sf − lossy) excludes zero; ≥2 models | **PARTIAL — deepseek cleared, qwen confounded** | `ROADMAP.md` M4 |
| M5 — boundary arm | cliff exists + direction + crossover tracks budget | **REPRODUCED** | `ROADMAP.md` M5 |

### Headline numbers

**Fact** — claim 1, wall grid at g ∈ {0.1, 0.3}, all three models
([`ROADMAP.md` M1 verdict table](../ROADMAP.md)):

| model | lossy RR | source_first RR | gap (Newcombe) |
|---|---|---|---|
| llama | 0/40 W[0%, 8.8%] | 40/40 | +100% [+87.6%, +100%] |
| deepseek | 1/90 W[0.2%, 6.0%] (escalated) | 40/40 | +99% [+88.8%, +99.8%] |
| qwen72b | 0/40 W[0%, 8.8%] | 40/40 | +100% [+87.6%, +100%] |

**Fact** — claim 3, deepseek only ([`ROADMAP.md` M2 D17](../ROADMAP.md)):
lossy 52/90 wrong emissions vs blank 0/40. Gap +58%, Newcombe [+44.2%, +67.5%].
33 of the 52 were exact attractor re-emissions of the planted value.

**Fact** — M5 boundary, deepseek on arithmetic
([`ROADMAP.md` M5 grid table](../ROADMAP.md)):

| source size N | B=300 | B=600 |
|---|---|---|
| 2 | 20/20 | 20/20 |
| 4 | 20/20 | 20/20 |
| 6 | **0/20** | 20/20 |
| 12 | 0/20 | 19/20 |
| 16 | 0/20 | **0/20** |
| crossover | **N=4** (paper ≈5) | **N=12** (paper ≈14) |

Full-vs-partial mechanism: 139/140 vs 0/108, Δ+99% [+94.6%, +99.9%].

### What each milestone cost

**Fact** — measured spend from the per-milestone cost ledgers in [`ROADMAP.md`](../ROADMAP.md):

| Milestone | Measured cost | Running total |
|---|---|---|
| M0 — fit-pilot | ≈ $0.165 | $0.165 |
| M1 — the wall | ≈ $0.450 | $0.615 |
| M2 — the controls | $0.293 | $0.908 |
| M3 — cross-check + capstone | $0.056 | $0.964 |
| M4 — logic family (PARTIAL) | $0.433 | $1.397 |
| M5 — boundary arm | $0.726 | **≈ $2.13** |

**Fact** — total ≈ $2.13 against KICKOFF's "likely under $10" envelope
([`DECISIONS.md` D31](../DECISIONS.md)).

### Pre-registration accuracy

**Fact** — the paper's primary model is llama-3.1-8b-instruct;
[`DECISIONS.md` D3](../DECISIONS.md) adopted the paper's own trio.

**Fact** — qwen-2.5-7b fired the D8 drift-take trigger (5/20 takes) and was replaced by
qwen-2.5-72b-instruct; the substitution is labeled in every table as a 10×-size
same-family stand-in, never as the paper's model
([`DECISIONS.md` D12](../DECISIONS.md)).

**Inference** — the KICKOFF flag that "logic is the one place a partial/null was ever
plausible" proved accurate: M4 is the project's only PARTIAL verdict. This is
consistent with the paper's reported softer logic wall (lossy ≈0.12–0.25 vs sf ≈0.67)
vs the hard arithmetic wall (lossy ≈0.00 vs sf ≈0.99–1.00). Rests on
[`ROADMAP.md` post-v1 fork](../ROADMAP.md) and [`DECISIONS.md` D25](../DECISIONS.md).

**Fact** — the one design decision reversed mid-project was M5's sweep axis: signed
D28-A (fix N, sweep budget) became D28-B (grow N at two budgets) when a free paper
extraction found the author's own design was B. Reversed before any paid run;
documented in [`DECISIONS.md` D28](../DECISIONS.md).

### One surprise finding per milestone

**Fact (M0)** — deepseek's initial AMBER drift-take verdict (13/20) was a parser artifact:
`ANSWER: \$197` was being read as no-commit. Rescoring archived evidence: 20/20 GREEN.
Documented in [`ROADMAP.md` M0 correction](../ROADMAP.md) and [`LEARNING.md` M1](../LEARNING.md).

**Fact (M1)** — deepseek's lossy@0.1 produced one "reclaim" — a lucky confabulation of a
round number with no source in context. Escalated per the pre-committed ladder; cleared at
1/90 [0.2%, 6.0%]. Source: [`ROADMAP.md` M1 D14](../ROADMAP.md).

**Fact (M4)** — on ordering logic puzzles, the directed correction ("the X-vs-Y order was
wrong") functions as a flip instruction. qwen obeyed it, inflating lossy RR and deflating
source_first RR — the confound that produced M4's PARTIAL verdict. Diagnosed at the
mandatory N=20 checkpoint hand-read; source: [`ROADMAP.md` M4](../ROADMAP.md),
[`DECISIONS.md` D25 outcome](../DECISIONS.md).

**Fact (M5)** — past the source-size cliff, source_first emits a confident *wrong* total
(partial sum of available items) rather than abstaining — the silent mis-sum.
`lossy_padded` at the same budget sits at 0/20. Source: [`ROADMAP.md` M5](../ROADMAP.md).

## Sources
- [`ROADMAP.md`](../ROADMAP.md) — milestone status table and per-milestone cost ledgers, verdict tables, checkpoint records
- [`DECISIONS.md`](../DECISIONS.md) — D1–D31, all decision outcomes including D28 reopen
- [`docs/KICKOFF.md`](../docs/KICKOFF.md) — pre-registered claims, success criteria, riskiest assumptions
- [`LEARNING.md`](../LEARNING.md) — teaching notes per milestone, surprise findings

## Uncertainties & contradictions

**Unresolved** — Kyle's recall-question answers for M3–M5 remain open in `LEARNING.md`
(project is closed; they are durable open items, not blockers).

**Fact** — the paper (arXiv v2) and the author's README disagree in the last digit on three
wall cells (paper lossy@0.3 0.01, sf 0.99/0.99 vs README 0.00, 0.96/1.00); the comparison
table in ROADMAP M3 carries the paper's values with a footnote. Source: [`ROADMAP.md` M3 footnote 4](../ROADMAP.md).

## Related pages
- [Methodology-Guardrails](Methodology-Guardrails.md)
- [Cross-Check-Against-Author-Code](Cross-Check-Against-Author-Code.md)

## Relevance to current work
This project is CLOSED (D31, 2026-07-09). A future reader would come here to get the
full measurement picture in one place — either to compare against a new paper's claims,
to assess which arms are worth extending in a successor project, or to evaluate the
pre-registration vs outcome story as a methodology case study.

_Last reviewed: 2026-07-26_
