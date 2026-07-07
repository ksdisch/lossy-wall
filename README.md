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
llama 14/20 (green) and deepseek **20/20** (green — first read 13/20 amber through a
parser blindspot on its LaTeX-escaped ANSWER lines, corrected during M1; see
ROADMAP's † note). The disposition probe reproduced the title claim's shape at full
strength on deepseek: lossy note at the wall → 11/12 confident wrong answers; blank
memory → 12/12 abstentions (Newcombe [+55%, +99%], corrected likewise). llama shows
the paper's predicted abstainer null (+1/12). Verdict
tables, cost ledger, and the qwen-slot story: `ROADMAP.md`.*

*Status: **M1 complete (2026-07-06)** — **claim 1 (the wall) CLEARED, 3 of 3 models.**
At matched character budget, directed corrections reclaim 1/290 lossy-note trials
(llama 0/80, deepseek 1/130 after its pre-committed escalation, qwen-2.5-72b 0/80)
vs **240/240** source-first trials; every lossy Wilson-95 upper bound sits under the
pre-committed 0.10 ceiling and every Newcombe gap floor is above +87%. The roster's
third slot resolved GREEN (D13: 72b took 18/20; labeled a same-family 10× substitute).
Mid-milestone, the mandatory checkpoint hand-read caught a live parser blindspot
(deepseek's LaTeX-escaped `ANSWER: \$…`), whose fix revised M0's deepseek take
verdict upward to 20/20 GREEN — details in ROADMAP's † note. The wall figure:
[`docs/figs/m1-wall.png`](docs/figs/m1-wall.png). M1 spend ≈ $0.45; project ≈ $0.62.*

*Status: **M2 complete (2026-07-07)** — **claim 2 (content, not length) CLEARED,
3 of 3 models; claim 3 (worse than empty — the title claim) CLEARED on deepseek.**
The budget-match control: padding the lossy note to the source-first note's length
rescued nothing (2/350 padded reclaims, both hand-read lucky guesses; every padded
cell contained inside the pre-committed ±10% of plain lossy, both escalations
resolving at 1/90) while source_first beats the padded note by ≥ +87.6% everywhere.
The emission gap, counted blind against M1's archived rows only after the blank arm
reached its final N: lossy 52/90 confident wrong answers vs blank **0/40** (40/40
explicit declines) — gap +58%, Newcombe [+44.2%, +67.5%]. The knob fills complete
the committed figure ([`docs/figs/m2-knob.png`](docs/figs/m2-knob.png),
[`docs/figs/m2-emission.png`](docs/figs/m2-emission.png)); llama's high-g dip is
real model behaviour, documented in the checkpoint record. M2 spend $0.29 measured;
project ≈ $0.91. Next: **M3 — the cross-check cell + capstone** (needs its
start-of-stage brief).*

The docs spine: [`docs/KICKOFF.md`](docs/KICKOFF.md) (approved scope, phased plan, gate
record — the source of truth) · [`DECISIONS.md`](DECISIONS.md) (running ledger, D1–D18)
· [`ROADMAP.md`](ROADMAP.md) (milestone status + verdict tables and cost ledgers) ·
[`LEARNING.md`](LEARNING.md) (teaching notes + vocabulary) ·
[`docs/M0-BRIEF.md`](docs/M0-BRIEF.md) (the M0 start-of-stage brief) ·
[`docs/M1-BRIEF.md`](docs/M1-BRIEF.md) (the M1 start-of-stage brief, signed) ·
[`docs/M2-BRIEF.md`](docs/M2-BRIEF.md) (the M2 start-of-stage brief, signed).
