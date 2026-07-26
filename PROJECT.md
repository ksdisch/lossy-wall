# PROJECT.md

## Purpose
Reproduce and measure, at hobby scale, the **Brittle Memory** effect from arXiv [2606.25449](https://arxiv.org/abs/2606.25449) ("Reclaim Evaluation: A Lossy Memory Is Worse Than an Empty One"): at a matched memory budget, a lossy note that keeps a wrong conclusion but drops its recomputable source makes the error uncorrectable, while a source-first note at the same budget stays fully correctable.

## Scope
**In scope (as executed):** v1 = arithmetic ledgers only, g ∈ {1.0, 0.6, 0.3, 0.1}, policies lossy / lossy_padded / source_first (matched char budget) + blank at the wall, directed corrections only, cheap OpenRouter models; post-v1 gated extensions M4 (logic family) and M5 (source-size boundary arm) were both executed. Judge-free exact-match scoring, Wilson/Newcombe CI gates, anti-rig validator suite.

**Out / never:** LLM-judge grading; point-estimate claims (direction + structure only); frontier-model spend; importing the author's `reclaim-eval` package into harness code (cross-check oracle only, per D1).

## Current status
**Complete** — closed 2026-07-10 at D31 (Fact: DECISIONS.md D31; verified at seed-hunt). All three pre-registered v1 claims REPRODUCED at their pre-registered bars, independent-build cross-check AGREE (6/6 gated cells); M4 logic family PARTIAL; M5 boundary arm REPRODUCED. Total spend ≈ $2.13 of the "under $10" budget. Succeeded in the repro lineage by ghost-patch, then dim-stage.

## Next actions
1. None — the phased plan is exhausted and the project is closed; new work would be a deliberate reopen.
2. Housekeeping only: PR [#34](https://github.com/ksdisch/lossy-wall/pull/34) (replication paper + presenter brief, branch `docs/paper-presenter-brief`) is still open and awaiting merge.

## Boundaries
- Zero Anthropic/OpenAI spend; cheap models via OpenRouter only (key in gitignored `.env`).
- Statistics are the binding constraint (N ≥ 20/cell, Wilson decides gates per D4), not code or cost.
- `docs/KICKOFF.md` is the source of truth for scope; scope decisions there are settled.
- The author's `reclaim-eval` clone stays an isolated cross-check oracle — never a dependency.
