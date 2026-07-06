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

All under pre-committed CI gates, on ≥2 of 3 models unless stated
(llama-3.1-8b-instruct / deepseek-chat / qwen-2.5-7b, via OpenRouter):

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

*Status: kicked off 2026-07-06 — scaffold only, no harness code yet. Building starts at
**M0, the fit-pilot** (drift-take pilot + disposition probe, per-model kill/swap
triggers armed).*

The docs spine: [`docs/KICKOFF.md`](docs/KICKOFF.md) (approved scope, phased plan, gate
record — the source of truth) · [`DECISIONS.md`](DECISIONS.md) (running ledger, seeded
with the kickoff's D1–D4).
