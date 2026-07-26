# History — lossy-wall

> How this project got here: a chronological narrative of eras and milestones,
> reconstructed from merged PRs, git history, wrap logs, and the decision ledger.
> PR numbers, merge dates, tags, and SHAs are **Fact** by construction; rationale
> lines carry explicit labels (**Fact** when quoted from a PR body/ADR, **Inference**
> when reconstructed). Decisions are anchored by ID to the project's decision
> ledger (root `DECISIONS.md`, D1–D31) — never restated here. **Append-only:** new
> milestones are added at the bottom (above the Mining coverage footer); existing
> entries are never rewritten.

## Origin — 2026-07

Third rung of the reproduce-and-measure lineage (forge-gap → decay-pin), picked via
`/seed-hunt` the same day decay-pin closed: reproduce the **Brittle Memory** effect
(arXiv 2606.25449) at hobby scale — a lossy note that keeps a wrong conclusion but drops
its recomputable source makes the error uncorrectable, worse than an empty memory.
First commit `e431677` (2026-07-06, kickoff scaffold); brief at `docs/KICKOFF.md`.
The four kickoff-gate choices — independent harness + one cross-check cell, the narrow
v1 cut, the paper trio roster, Wilson/Newcombe-decides — see D1–D4 in `DECISIONS.md`.

## Era: v1 — the three claims (2026-07-06 – 2026-07-08)

Four milestones in three days, run on a fixed per-stage rhythm: start-of-stage brief with
proposed decisions → Kyle signs → free ($0) TDD build → paid runs judged only by
pre-committed gates → closing PR carries evidence + ledger + spine. By the end, all three
headline claims were REPRODUCED and the author-harness cross-check agreed.

### M0 signed and the free half built — 2026-07-06
- **Landed:** M0 fit-pilot brief + D5–D9 sign-off; decay-pin plumbing ported (client/stats/ping); problems generator, four note policies, ANSWER-line grader; session frames + per-trial source gate + anti-rig validator suite (PR #1, #2, #3, #4, #5)
- **Why:** free-before-paid — anti-rig 3/3 and pytest green before the first API call [Fact — PR #1 body] — see D5–D9 in `DECISIONS.md`

### M0 closed two-model — 2026-07-06
- **Landed:** paid pilots run and judged — llama GREEN, deepseek AMBER, qwen-7b TRIGGER → swap saga → infrastructure block; deepseek disposition probe GREEN (the title claim's shape at full strength); two live scoring bugs TDD-fixed; ≈$0.165 (PR #6)
- **Why:** both riskiest assumptions (drift takes; the gap is powerable at hobby N) answered YES before any grid spend [Fact — PR #6 body] — see D8–D12 in `DECISIONS.md`

### M1 signed; evidence made durable — 2026-07-07
- **Landed:** M1 brief + D13–D15 recorded; `evidence/m0/` committed (70 JSONLs), `uv.lock` tracked, session-log text tracked (PR #7, #8)
- **Why:** a fresh container had silently dropped all gitignored run evidence [Fact — PR #7 body] — see D13–D15 in `DECISIONS.md`

### Parser blindspot fixed — deepseek verdicts corrected upward — 2026-07-07
- **Landed:** `parse_answer` widened for LaTeX-escaped dollars (`ANSWER: \$197`); M0 deepseek rescored 13/20 AMBER → 20/20 GREEN; regression tests pinned (PR #10)
- **Why:** M1's mandatory checkpoint hand-read caught it before the grid spent a token — deterministic fakes validate mechanics, not behavior [Fact — PR #10 body]

### M1 closed — claim 1 (the wall) CLEARED 3/3 — 2026-07-07
- **Landed:** wall-grid driver + close: lossy reclaims 1/290 roster-wide vs source_first 240/240; wall figure; M1 ≈ $0.45 (PR #9, #11)
- **Why:** judged only by the pre-committed N-ladder, one escalation fired — see D14 in `DECISIONS.md`

### M2 closed — claims 2 and 3 CLEARED — 2026-07-07
- **Landed:** controls grid (D16 ladder pre-committed in code): claim 2 (content, not length) CLEARED 3/3; claim 3 (worse than empty) CLEARED on deepseek — 52/90 wrong emissions on lossy vs 0/40 on blank, counted blind (PR #12, #13, #14)
- **Why:** blank-arm counting rule committed before the comparator split was tallied — see D16–D18 in `DECISIONS.md`

### M3 closed — cross-check AGREE 6/6; v1 complete — 2026-07-08
- **Landed:** author's harness run unmodified as oracle (4,896 calls, $0.055): all six overlap cells' Newcombe intervals contain zero; `bootstrap.py` appendix (39 rows, zero Wilson-vs-bootstrap disagreements); comparison table + capstone figure; project ≈ $0.97 (PR #15, #16, #17, #18, #19, #20, #21)
- **Why:** the cross-check is a protocol-fidelity line, not a re-judging — see D19–D22 in `DECISIONS.md`
- **Tradeoff:** verdicts stand as judged either way; disagreement would have triggered a protocol audit, not a re-score [Fact — PR #15 body]

## Era: Gated extensions (2026-07-08 – 2026-07-09)

The two post-v1 arms D2 had gated on "only if the effect shows." Kyle picked M4 (logic
family) at the post-v1 fork, then M5 (source-size boundary). One PARTIAL, one REPRODUCED.

### M4 opened and free-built — the soft wall — 2026-07-08
- **Landed:** M4 brief + D23–D26; logic problems/generators/notes/anti-rig extensions; `m4.py` driver with the gap/separation gates and REPRODUCED/PARTIAL/NULL/DISCREPANT mapping pre-committed as pure functions; paper Table 6 anchor double-extracted (PR #22, #23, #24, #25, #26, #27)
- **Why:** claim-2 equivalence at δ=0.10 is unpowerable at hobby N on logic, so the gate was reformulated to separation before any data existed [Fact — PR #22 body] — see D23–D26 in `DECISIONS.md`

### Take-probe format bug fixed; llama sits out — 2026-07-08
- **Landed:** `TAKE_PROBE_LOGIC` made format-explicit after a false 0/20 llama TRIGGER; re-pilot 9/20 — the trigger is real; M4 proceeds two-model (PR #28)
- **Why:** the probe had silently dropped D11's format-explicit contract; the checkpoint hand-read caught it — see D24 in `DECISIONS.md`

### M4 closed — PARTIAL — 2026-07-09
- **Landed:** deepseek clears both claims (textbook worse-than-empty on logic); qwen72b confounded by a real ordering-puzzle × directed-correction interaction; soft-wall figure; M4 $0.433 (PR #29)
- **Why:** with the anchor model out and one of two survivors confounded, the ≥2-model bar maps to PARTIAL — see D25–D26 in `DECISIONS.md`

### M5 signed and free-built; D28 reopened A→B — 2026-07-09
- **Landed:** boundary-arm brief + complete $0 build; the paper-boundary extraction found the author's released sweep uses grow-N-at-two-budgets, overturning the signed fixed-N design before any spend (PR #30)
- **Why:** reproduce the paper's actual design, not the brief's assumption of it — see D27–D30 (esp. the D28 reopen) in `DECISIONS.md`

### M5 closed — boundary REPRODUCED — 2026-07-09
- **Landed:** source_first cliffs to 0 past the budget; crossover tracks the budget (N=4 @ B=300 vs N=12 @ B=600, paper ≈5/≈14); silent mis-sum confirmed on real deepseek (PR #31)
- **Why:** every D29 gate cleared at judged N=20 — see D29 in `DECISIONS.md`

## Era: Close-out and documentation (2026-07-09 – 2026-07-26)

### Project closed — 2026-07-10
- **Landed:** D31 recorded + PROJECT CLOSED banner in ROADMAP.md; stale M4 row fixed; total measured spend ≈ $2.13; next move `/seed-hunt` (PR #32, #33)
- **Why:** the phased plan is exhausted — v1 claims 1–3 REPRODUCED + cross-check AGREE, M4 PARTIAL, M5 REPRODUCED — see D31 in `DECISIONS.md`

### Project wiki initialized — 2026-07-26
- **Landed:** PROJECT.md, HANDOFF.md, Sources.md + CLAUDE.md wiring (PR #35)
- **Why:** fleet-wide wiki-init pass over the closed repo [Fact — PR #35 body]

---

## Mining coverage
_Backfilled 2026-07-26 by project-wiki BACKFILL. Entries after this date are
appended live by MAINTAIN._
- PR title sweep: all 34 merged PRs — no cap
- Deep reads: 20 of 34 PRs (size/label/title signal; cap 20)
- Also swept: git log (merges/no-merges), tags (none exist), `DECISIONS.md` D1–D31 (anchor-only), `ROADMAP.md`, `docs/KICKOFF.md`, wrap logs in `docs/session-logs/`, `LEARNING.md`
- Not mined: open PR #34 (docs/paper-presenter-brief, held for Kyle's review), closed-unmerged PRs, issues
