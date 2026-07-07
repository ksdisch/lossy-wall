# lossy-wall

Reproduce and measure, at hobby scale, the **Brittle Memory** effect (arXiv
[2606.25449](https://arxiv.org/abs/2606.25449), *"Reclaim Evaluation: A Lossy Memory Is
Worse Than an Empty One"*): at a matched memory budget, a lossy note that keeps a wrong
conclusion but drops its recomputable source makes the error uncorrectable — the model
re-emits the stale value where an *empty* memory would abstain — while a source-first
note at the same budget stays fully correctable.

## Why

Compress-toward-the-conclusion is what shipped memory systems do today, and this paper
says that policy is *worse than remembering nothing* once the remembered conclusion is
wrong. The deltas are enormous (reclaim rate 0.00 vs 0.99–1.00 at the wall), scoring is
judge-free exact-match, the cure is training-free (a compression-policy choice), and the
paper's own primary model is a cheap 8B — hobby scale is the paper's *native* scale, not
a compromise. It is also a single-author, unreplicated paper: a careful independent
replication is genuinely useful, and **a null is pre-committed as a reportable verdict**.

Third rung of the reproduce-and-measure lineage:
[forge-gap](https://github.com/ksdisch/forge-gap) →
[decay-pin](https://github.com/ksdisch/decay-pin) → **lossy-wall**.

## What success looks like (v1)

All under pre-committed CI gates, on ≥2 of 3 models unless stated — the roster began
as the paper trio (llama-3.1-8b-instruct / deepseek-chat / qwen-2.5-7b, via
OpenRouter); qwen-2.5-7b fired its M0 drift-take trigger and v1 currently proceeds
two-model, with a qwen-2.5-72b re-attempt deferred to the M1 brief (D12):

1. **The wall** — at wall integrity (g ≤ 0.3), the lossy policy's reclaim rate has a
   Wilson CI consistent with ~0, *and* the Newcombe interval on (source_first − lossy)
   excludes zero.
2. **Content, not length** — at the wall, (lossy_padded − lossy) lands inside a
   pre-committed equivalence margin *and* (source_first − lossy_padded) excludes zero.
3. **Worse than empty** (the title claim) — on ≥1 disposed-to-answer model, the
   Newcombe interval on wrong-emission rate (lossy − blank) excludes zero.

Plus the g-sweep wall figure, a labeled comparison table against the paper's numbers,
and the **cross-check cell**: our independently built harness vs the author's released
[reclaim-eval](https://github.com/collapseindex/reclaim-eval) on one overlapping cell —
agreement or disagreement reported either way. Non-goals, always: direction + structure,
never point estimates; no LLM-judge grading, ever; zero frontier spend in v1.

*Status: **M0 complete (2026-07-06)** — machinery green (anti-rig 3/3, 64 tests, $0
until gated), both riskiest assumptions answered YES for ≈ $0.17 total. Drift takes:
llama 14/20 (green) and deepseek 13/20 (amber — a weak-ish take, so deepseek's
session-1 generation runs ~1.5× inflated from M1 on, per D8). The disposition probe
reproduced the title claim's shape at full strength on deepseek: lossy note at the
wall → 10/12 confident wrong answers; blank memory → 12/12 abstentions (Newcombe
[+46%, +95%]). llama shows the paper's predicted abstainer null (+1/12). Verdict
tables, cost ledger, and the qwen-slot story: `ROADMAP.md`. Now running: **M1, the
wall** — brief signed 2026-07-06 ([`docs/M1-BRIEF.md`](docs/M1-BRIEF.md), D13–D15
recorded in `DECISIONS.md`).*

The docs spine: [`docs/KICKOFF.md`](docs/KICKOFF.md) (approved scope, phased plan, gate
record — the source of truth) · [`DECISIONS.md`](DECISIONS.md) (running ledger, D1–D15)
· [`ROADMAP.md`](ROADMAP.md) (milestone status + M0 verdicts and cost ledger) ·
[`LEARNING.md`](LEARNING.md) (teaching notes + vocabulary) ·
[`docs/M0-BRIEF.md`](docs/M0-BRIEF.md) (the M0 start-of-stage brief) ·
[`docs/M1-BRIEF.md`](docs/M1-BRIEF.md) (the M1 start-of-stage brief, signed).
