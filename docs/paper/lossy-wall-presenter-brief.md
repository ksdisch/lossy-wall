# Presenter Brief — defending the lossy-wall paper, claim by claim

*Companion to `lossy-wall-paper.md` (2026-07-09). Everything here is in the paper; this is the fluent version — what to say out loud, and what to say when pushed.*

## The 30-second version

"I independently replicated a published result about LLM memory. When a memory system compresses a conversation into a note, it can keep the *conclusion* or keep the *source facts* — same character budget either way. The paper says: if the remembered conclusion is wrong, the conclusion-keeping note is **worse than no memory at all** — the model confidently repeats the stale wrong answer even when you tell it exactly where the error is, while a model with an empty memory just says it doesn't know. I rebuilt their whole experiment from the paper's description, pre-registered every statistical gate before spending a cent, and got the same thing: corrections fixed 1 of 290 conclusion-only trials versus 240 of 240 source-keeping trials. Total cost about two dollars."

The one framing rule that binds everything: **"I reproduced and measured a published finding — here is the narrow, measured slice."** Never "I discovered this." The novelty is the independence, the pre-registration, and the honesty of the record — not the effect.

## The story arc (60 seconds, if they want more)

Three claims, one cross-check, two extensions. Claim 1: the wall — at low memory integrity, lossy notes are uncorrectable, source-first notes perfectly correctable. Claim 2: it's the *content*, not the length — padding the lossy note to the source note's exact size rescues nothing. Claim 3, the title claim: the lossy note is worse than an *empty* one. Then the cross-check: the author's own released code, run unmodified on their own cell sizes, agreed with my build on all six overlap cells. Then two extensions: the effect generalizes to logic puzzles (partially — one model clean, one confounded, reported honestly), and the fix has a measurable *boundary* — grow the source past the note budget and source-first itself cliffs to zero, failing silently.

## Claim-by-claim defense

### Claim 1 — the wall (REPRODUCED, 3/3 models)

**The number:** lossy notes: 1 reclaim in 290 trials (that one was a hand-read lucky guess, kept under strict scoring). Source-first: 240/240. Every between-arm gap has a 95% floor of at least +87.6%.

**The gate, in plain terms:** each lossy cell's Wilson 95% interval had to have an *upper bound* below 10% (you can never prove a rate is exactly 0 — you can only show it's consistent with ~0), and the interval on the difference had to exclude zero. Both, at both wall integrity levels, on at least 2 of 3 models. All committed in writing before the data existed.

**If pushed — "one lossy reclaim, so it's not really zero?"** Correct — the claim is a *ceiling*, not "exactly 0." That stray triggered a pre-committed escalation: the cell ran to N=90, gained nothing, cleared at [0.2%, 6.0%]. A stray neither kills the claim nor gets waved through; it buys a bigger sample.

### Claim 2 — content, not length (REPRODUCED, 3/3 models)

**The number:** padded cells reclaimed 2/350 (both hand-read lucky guesses); every padded cell sat inside a pre-committed ±10% of plain lossy, while source-first beat the padded note by ≥ +87.6% everywhere.

**The point to land:** this kills the objection "the source note is just longer." Same character budget, only the *content* differs.

**If pushed — "how do you prove two things are the same?"** Not by failing to find a difference. Equivalence needs a **containment gate**: the interval on (padded − lossy) must sit entirely inside a band (±0.10) that was fixed *before the project's first paid API call*. Land outside the band and the claim dies — that's what makes "they're the same" falsifiable.

### Claim 3 — worse than empty (REPRODUCED on deepseek; predicted nulls on the other two)

**The number:** over identical induced-error histories, deepseek with a blank note declined 40/40 times. With the lossy note it emitted a confident wrong answer 52/90 times — 33 of them the exact stale value it committed in session 1. Gap +58%, 95% CI [+44.2%, +67.5%].

**Why one model is enough:** the pre-registered bar was ≥1 *answering-disposed* model, because the paper itself predicts abstainer models show no gap. llama and qwen72b are abstainers, showed the predicted null, and those nulls are reported plainly — they confirm the paper's shape rather than undermining it.

**Two honest details to volunteer before anyone asks:** the two arms were sampled on different dates (same model, route, temperature, and underlying trajectories — pre-registered as a caveat); and the counting rule was committed while the archived comparator's split was still uncounted, with the no-peek enforced *in code* — the judge refuses to tally before the blank arm's final N.

### The cross-check — AGREE, 6/6 cells

**What it is:** the author's own released harness, unmodified, in its own environment, run on the paper's own cell economy (n=96/cell, ~4,900 calls, $0.055). Pre-committed criterion: agreement means the interval on (their rate − ours) contains zero on all six wall overlap cells. All six did — e.g., their lossy 0/96 vs our 0/40; their source-first 96/96 vs our 40/40.

**Why it matters — the line to use:** "A replication is not a re-run. Re-running their code tests their code. I built from the paper's *description* and met their code at one cell — that tests whether the paper's words are sufficient instructions. They were."

**And the oracle isn't sacred:** the same milestone proved their parser mis-reads `ANSWER: \$197` (LaTeX-escaped dollar) as an abstention — mechanically: 0/8 of our archived escaped replies parse in their parser, 8/8 in ours — and their table-reproduction script fails on their own shipped repo. Direction bounded: that bug can only have *shrunk* their published lossy-vs-blank gap, so their +0.83 is a floor if it bit at all.

### Extension 1 — logic family (PARTIAL — say this proudly, not apologetically)

**The result:** deepseek cleared both claims decisively (source-first 60/60 at both wall g; gaps +35% and +77%, both excluding zero) and showed the thesis in a new form — a note keeping the *corrupted premise* made the error stickier (padding it drove inheritance from 45% to 70%). qwen did not clear, and the hand-read found the real reason: on ordering puzzles, the correction "the X-vs-Y order was wrong" acts as a **flip instruction**. qwen flips whatever it's shown — including flipping the *true* fact into the error. deepseek re-derives and resists.

**The tell worth explaining:** every qwen source-first error was exactly the planted value, and *zero* were novel errors — proof the errors were manufactured by the correction-flip, not by mis-solving.

**If pushed — "so it failed?"** No: one clean model of the two the pre-committed ≥2-model bar needs is, by the pre-committed vocabulary, PARTIAL. A replication that can only say "reproduced" isn't a measurement. The confound is a first-class finding about directed corrections on ordering tasks.

### Extension 2 — the boundary (REPRODUCED — where the fix fails)

**The result:** hold the note budget fixed, grow the receipt. Past the point where the note can't keep every line item, source-first cliffs from 20/20 to 0/20. Run *two* budgets and the cliff *moves*: crossover at 4 items under budget 300, 12 items under budget 600 (paper's anchors: ≈5 and ≈14). If this were "big problems are hard," the cliff wouldn't move with the budget. Mechanism: full source 139/140 reclaims, partial source 0/108.

**The keeper detail:** past the cliff the model doesn't say "I can't" — it confidently sums the *partial* source to a wrong total (neither the truth nor the planted value: the sum of what survived). Silent failure, worse than empty. Hand-verified as genuine mis-summing, not a scoring artifact.

## Cross-cutting questions you will get

**"Why should I trust scoring with no human or LLM judge?"** Exact-match on a demanded `ANSWER:` line, plus an anti-rig suite: a deterministic fake model that can only reclaim when the source tokens are literally present — so the pipeline can't be fooled by a model that pattern-matches. But the honest lesson is that judge-free is not worry-free: three scoring bugs were caught during the project, all by the *mandatory human hand-read* at checkpoints, and all corrected with the record kept (one even revised an earlier verdict *upward*). Validators prove the machinery; eyes prove the readout.

**"Temperature 0 — so it's deterministic?"** No — same prompt, temperature 0, different replies across runs (provider-side serving variation). That's why every result rides on N and proportion intervals, not on single greedy samples.

**"Why Wilson intervals instead of the paper's bootstrap?"** The wall cells live at 0% and 100%, exactly where the bootstrap degenerates: every resample of 0/40 is 0/40, so it reports [0.000, 0.000] — maximal confidence where evidence is thinnest. Wilson says [0%, 8.8%]. The choice was pre-committed, and an appendix re-typing the author's own bootstrap over all 39 gate-driving numbers found zero cases where the method choice changed a verdict.

**"What's the weakest part?"** Offer these unprompted if the conversation is serious: hobby N (wide intervals off the extremes; anything unpowerable was pre-registered as descriptive, not gated); the qwen slot is a 10×-size same-family substitute, so the paper's qwen-7b has no comparable cell; the paper's own table ran at temperature 0.7 vs our 0.0 (labeled, never point-matched — direction and structure only); planted errors buy clean measurement at the cost of ecological generality.

## Numbers to have cold

- **1/290 vs 240/240** — claim 1, lossy vs source-first, all models pooled.
- **2/350, ±10% band, ≥ +87.6% separation** — claim 2.
- **52/90 vs 0/40, gap +58% [+44.2%, +67.5%]** — claim 3, deepseek.
- **6/6 intervals contain zero** — cross-check AGREE; oracle run $0.055, n=96/cell.
- **+35% / +77% (deepseek) vs −3% / −2% (qwen)** — M4 gaps → PARTIAL.
- **Crossover 4 → 12 as budget 300 → 600; 139/140 vs 0/108** — M5 REPRODUCED.
- **≈ $2.13** — total measured spend, all milestones, against a "likely under $10" plan.

## Vocabulary (one line each, in your own words)

- **Reclaim rate (RR)** — of the trials where the model committed to the planted wrong value, the fraction where a directed correction recovers the truth.
- **Drift / take** — the model swallowing the planted wrong premise; every measurement conditions on it.
- **Integrity g / the wall** — what fraction of memory survives compression; below g=0.5 the lossy note loses the source facts.
- **Attractor** — the stale wrong value the model gravitates back to.
- **Wilson / Newcombe** — the right intervals for rates and for differences between rates; well-behaved at 0% and 100%, where this experiment lives.
- **Containment vs excludes-zero** — proving sameness (interval inside a pre-set band) vs proving difference (interval avoids zero). Claim 2 needed one of each.
- **Silent mis-sum** — past the boundary, source-first confidently totals the partial source instead of abstaining.
