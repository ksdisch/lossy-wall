# M4 Start-of-Stage Brief — the logic family (the soft wall)

*Written 2026-07-08 · status: **signed & CLOSED — M4 PARTIAL (2026-07-08)** — D23–D26 signed;
outcomes in `DECISIONS.md`, verdict + cost ledger in `ROADMAP.md` M4 · scope source of truth:
`docs/KICKOFF.md` (Milestone 4, gated) · format follows `docs/M1-BRIEF.md`.*

## What M4 is, in plain terms

v1 is closed: all three claims REPRODUCED, the cross-check AGREE, one legible deliverable
shipped for ≈ $0.97. KICKOFF gated two extensions on *"only if the effect shows"* — it
showed, decisively — and at the post-v1 fork (2026-07-08) Kyle picked **B: open M4, the
logic family** (the pick is recorded as D23's outcome once this brief signs).

M4 asks one question: **does the brittle-memory effect survive a change of task?** v1
measured it on *arithmetic ledgers* — a store receipt with a planted-wrong subtotal, where
the "source" you'd need to recompute is a set of numbers and prices. M4 swaps in the
paper's second task family: **constraint-deduction puzzles** ("Ana, Ben, Cleo each hold one
role; Ben is not the manager; Cleo is the auditor — who is the manager?"). A planted-wrong
clue ("a colleague says Ben is the manager") drifts the answer; the "source" you'd need to
re-derive is now *a set of logical relations, not a formula*. The answer is still a single
token from a closed set (Ana / Ben / Cleo), so scoring stays **judge-free** — no LLM judge,
ever (the project's iron rule).

**The twist that makes M4 worth doing — the wall is *soft* on logic.** On arithmetic the
wall is a cliff: drop the numbers and a lossy note reclaims ~0.00, the fix reclaims ~1.00.
On logic the paper finds the same *shape* but a *softer* floor — a strong model can
partially re-derive the answer from a corrupted relational clue in a tiny space, so lossy
doesn't collapse to zero. The paper's own third finding states it: *"The wall's hardness is
conditional. A clean 0.00 on arithmetic … and soft on logic … Same on both models, so it is
a property of the task, not the model."* This is precisely why the fork brief called M4
**the most falsification-shaped extension** — the one place in the whole study where a
PARTIAL or NULL was ever genuinely plausible. M4's job is to measure that soft wall
honestly, not to force it into the arithmetic mould.

## The paper's logic anchor (the target)

From the author's README wall table — directed-arm reclaim at the wall region, printed as
**g = 0.3 / 0.1** (memory integrity):

| model · task | lossy | lossy_padded | source_first |
|---|:--:|:--:|:--:|
| llama-3.1-8b · logic | 0.25 / 0.12 | 0.25 / 0.04 | **0.67 / 0.67** |
| grok-4.3 · logic | 0.42 / 0.50 | 0.38 / 0.50 | **0.92 / 0.96** |

Read this against the arithmetic wall (llama: lossy 0.00/0.00, sf 0.96/1.00): the *fix*
still wins big, but on logic the lossy floor sits at **0.12–0.25**, not zero, and the
source_first ceiling at **0.67**, not one. That is the soft wall, in numbers.

Three things to note before it anchors any gate:

- **Only llama is our roster ∩ the paper's logic anchor.** grok-4.3 is not in our frozen
  trio (llama / deepseek / qwen-2.5-72b-instruct, D13). So **llama·logic is the one cell
  with a published comparison target** — the natural cross-check anchor — while
  deepseek·logic and qwen72b·logic we measure *fresh* (still valuable: task-generality
  across our own roster, just with no paper number to sit beside).
- **These are README values; the paper (arXiv v2) may differ in the last digit.** M3's
  extraction caught exactly this on the arithmetic row (README sf 0.96/1.00 vs paper
  0.99/0.99). So M4 schedules a **verbatim arXiv v2 logic-table extraction** as a free step
  (rider a below), mirroring `evidence/m3/paper-extraction.md`, and sets its gates to be
  robust to last-digit noise.
- **The wall region is g ∈ {0.1, 0.3}, exactly as in v1** (D2's four-point knob; the wall
  cells are the two low-integrity points).

## The crux: what "soft wall" changes about the gates

The arithmetic claim gates do **not** transfer wholesale — and seeing *why* is half of M4.

**1. Claim 1's lossy ceiling is gone; the gap survives.** v1's claim 1 had two halves
(D14): *(a)* lossy is "consistent with ~0" — a ceiling of 0.10 on the Wilson upper bound —
and *(b)* the gap source_first − lossy excludes zero. On logic, half (a) is **false and
known-false**: llama lossy is 0.12–0.25, above the 0.10 ceiling. Demanding it would be
demanding the paper's own finding not hold. So M4 keeps the half that transfers — **the
gap** — and *reports* the soft floor instead of gating on it. And the gap is powerful even
at modest N (computed with our `stats.py`, using the paper's llama anchor as the modelling
assumption):

| gap sf − lossy | N=40 | N=60 |
|---|---|---|
| g = 0.3 (0.67 vs 0.25) | +0.43 [+0.21, +0.59] ✓ excludes 0 | +0.42 [+0.24, +0.56] ✓ |
| g = 0.1 (0.67 vs 0.12) | +0.55 [+0.34, +0.69] ✓ excludes 0 | +0.55 [+0.39, +0.67] ✓ |

The fix-beats-lossy signal clears at N=40. Bigger N buys precision on the *floor*, not the
gate.

**2. Claim 2's equivalence is unpowerable at hobby N — it must be reformulated.** v1's
claim 2 (D7/D16) tests that padding doesn't rescue via *equivalence*: the Newcombe interval
on (lossy_padded − lossy) must sit **entirely inside ±0.10**. That works when both rates
are ~0 (a tight interval hugging zero). At a *mid-range* rate it cannot — the CI is simply
too wide:

| padded ≈ lossy (both ~0.25) | Newcombe interval | inside ±0.10? |
|---|---|---|
| N = 40 | [−0.19, +0.19] | **no** |
| N = 60 | [−0.15, +0.15] | **no** |

To pull the equivalence band inside ±0.10 at a 0.25 base rate you'd need roughly **N ≥ 150
per arm** — outside this project's economy and pointless besides. So M4 **cannot** run the
arithmetic equivalence test. But the *separation* half still gates cleanly (source_first −
padded ≈ +0.42, the same shape as the gap above). The honest reformulation: **gate claim 2
on separation (sf > padded excludes zero); report the padded≈lossy overlap descriptively**
(both point estimates, both Wilson CIs, and the plain statement that they overlap — with the
pre-registered caveat that δ = 0.10 equivalence is unpowerable at this N on a mid-range
rate). This is the CLAUDE.md rule in action — *the binding constraint is the statistics, not
the code or the cost* — and it needs a fresh pre-commitment (D25), because D7's δ = 0.10 was
written for arithmetic.

**3. The chance floor — a closed answer set muddies raw reclaim rate.** A logic answer is
one token from a set of 3–5 options, so a pure guesser scores ~1/k correct (~0.20–0.33).
That means "reclaim rate" alone is a noisy read on logic: llama's lossy 0.25 is near the
guess baseline, and lossy 0.12 is *below* it (because a lossy note pulls the model toward
*inheriting the wrong option*, not guessing uniformly). Raw RR can't distinguish "re-derived
the answer" from "guessed lucky." The fix is the author's own **failure-mode taxonomy**
(from `logic_failmode.py`), which we adopt as the standard logic readout (rider b):

- **recov** — committed the *correct* token (= reclaim).
- **inherit** — committed the planted *drift* token (the worse-than-empty signal — the
  model swallowed the wrong clue).
- **novel** — committed a *different* wrong token.
- **abst** — no committed token (a hedge / refusal).

`recov` is still the reclaim rate the gap uses; but `inherit` vs `abst` is what tells the
worse-than-empty story on logic, and reading all four keeps the chance floor legible (a
guesser spreads across recov/inherit/novel; inheritance skews toward `inherit`).

## What v1 settled that M4 stands on (not re-litigated)

- **Roster frozen (D13): llama / deepseek / qwen-2.5-72b-instruct.** llama anchors the
  cross-check (paper's primary, and the only published logic comparison). qwen72b stays
  labelled everywhere as a same-family 10×-size substitute for the paper's qwen-7b, never as
  the paper's model. No roster change in M4.
- **Sampling (D10): temperature 0.0, max_tokens 600**, matching the author's harness. M4's
  driver imports the constants, never redefines them.
- **Readout idiom (D11) adapts, not reinvented.** v1's take-probe turn ("state the total as
  ANSWER: …") becomes, for logic, the author's own final restatement turn ("What single word
  should I write down as the answer?"), graded by a **closed-set single-token match** and
  never carried into session 2. Same principle: one strict parser everywhere, the take/read
  locus explicit.
- **Stats (D4): Wilson on cells, Newcombe on differences decide; bootstrap is robustness
  only.** The `bootstrap.py` appendix (D21) extends to M4's gated cells for free.
- **Evidence survives the machine (D15):** M4's paid JSONLs get committed to `evidence/m4/`
  in the closing PR; `uv.lock` and session-log text stay tracked.
- **The M0 scoring lesson binds harder on a new family.** Two live scoring bugs in v1
  (the cents trap; prose commits without ANSWER lines) sailed through the deterministic fake
  and were caught only by hand-reading real replies. A brand-new readout (single-token
  parsing, closed-option matching, four-way taxonomy classification) is exactly where the
  next such bug hides — so the N=20 checkpoint hand-read is **mandatory** before any logic
  cell scales, and its first job is bug-catching, not futility.
- **D6 — the author's code is a protocol reference, re-typed with attribution, never
  imported.** M4 re-types `PROBLEMS_LOGIC`, `FACTS_LOGIC`, `FOLLOWUPS_LOGIC`, the two
  generators (`gen_logic`, `gen_assign`), the text scorer, and the taxonomy classifier from
  the oracle clone into our harness with citing comments. `reclaim-eval` never enters
  `pyproject.toml`.
- **Not re-litigated:** v1's verdicts (claims 1–3 REPRODUCED, cross-check AGREE), D1–D22,
  the v1 scope, the arithmetic cells. Settled. M4 re-runs and re-judges **nothing** from v1.

## The design: logic problems, judge-free text scoring, one bank, the grid, the figure

Everything M4 needs is a *text-answer* sibling of machinery v1 already has:

- **Problems (new, re-typed per D6):** the 8 hand-written logic puzzles + the 8→32
  expansion (`gen_logic` 12 ordering + `gen_assign` 12 assignment, the author's seeds) into
  `problems.py`; `FACTS_LOGIC` (the clue set = the recomputable source) and `FOLLOWUPS_LOGIC`
  (commitment turns that re-affirm without re-solving). Registered under `TASKS["logic"]`.
- **The note builder extends to text (`notes.py`):** same g-threshold mapping as v1 —
  **lossy** keeps the committed drift token, sheds the clues; **source_first** keeps the
  `FACTS_LOGIC` clues, sheds the re-derivable conclusion; **lossy_padded** = lossy + neutral
  filler to source_first's length. The per-trial **source gate runs in both directions**
  exactly as v1 (`runner.verify_note_gate`): a lossy note must demonstrably lack the clues, a
  source_first note must carry them — every trial, mechanically.
- **The scorer extends to text (`grader.py`):** a single-token parser + closed-option match
  against the problem's own `options`, plus the four-way taxonomy classifier (recov / inherit
  / novel / abst) re-typed from `logic_failmode.py`. Refusal prose still parses to "no
  commit" (abst), so the paper's v2 loose-parser bug can't return through this door.
- **The bank (logic):** a pool of *taken* logic trajectories — session-1 conversations where
  the model committed to the planted drift token — shared across models on a fresh `m4-`
  problem schedule (D5 pairing: one taken trajectory feeds every policy × g cell for that
  trial). "Take" = session-1 committed to `drift`.
- **The grid + figure:** session 2 = `[system, note, directed correction]`, one call per
  trial, note gated per trial, reply scored and taxonomy-classified. The figure
  (`docs/figs/m4-logic-wall.png`): reclaim (recov) rate vs g per model with Wilson bars, plus
  a stacked taxonomy bar at the wall (recov/inherit/novel/abst) — the soft floor made
  visible.

## Decisions — D23–D26 (pick or veto; recommendation marked; numbering continues DECISIONS.md)

### D23 · M4 scope — how many arms to layer

The project builds the ugliest end-to-end version first and *adds no arm before the headline
reads honestly* (CLAUDE.md). M4's headline is the soft wall: does the fix generalize, and
how soft is the floor. Three tiers, each a superset of the last:

- **A. Core (Recommended).** The soft wall on all three models: **lossy / lossy_padded /
  source_first** at g ∈ {0.1, 0.3}, read through the four-way taxonomy, gated by D25; plus
  the **logic drift-take pilot** (D24) that must pass per model first. The taxonomy delivers a
  *descriptive* worse-than-empty read for free (the `inherit` fraction on each lossy cell),
  so the core already speaks to all three claims' shapes. *Merit:* the thinnest honest test
  of task-generality; one figure, one grid, cheapest evenings. *Trade-off:* no independent
  cross-check on the new family, and claim 3's worse-than-empty stays *descriptive* (taxonomy)
  rather than *gated* (a formal lossy-vs-blank interval).
- **B. Core + a llama·logic cross-check cell.** Add one run of the author's
  `run_pilot.py --real --task logic` on llama at their defaults (n=96), recounted and judged
  by D20's AGREE/DISCREPANT machinery — extending D1's promise to the second family, on the
  one model with a published anchor. *Merit:* the project's signature (two independent builds,
  one number apart) applied to the soft wall — the strongest evidence the softness isn't a
  bug in *our* build. *Trade-off:* one more oracle run (~$0.05–0.10, ~7 h background hum like
  M3) and its recount evening.
- **C. B + a gated claim-3 (blank/emission) arm on the emitter.** Add a logic **blank** arm
  and gate the wrong-emission gap (lossy − blank excludes zero) on whichever model the D24
  pilot shows *emits* on logic (deepseek is the v1 emitter; unproven on logic). *Merit:* the
  title claim, formally gated on the new family. *Trade-off:* the most speculative — it rides
  entirely on the pilot showing a logic emitter — and the biggest spend.

*Why A:* the guardrail is lean-first — *no extra arm before the headline gap reads honestly*
— and M4's headline is the fix-generalizes gap plus the soft-floor characterization. The
cross-check (B) and the formal claim-3 (C) are real arms to *layer*, exactly as M1→M2→M3
layered, once the core reads clean and Kyle wants them. Recommending A keeps M4 the thinnest
falsification slice and leaves B and C as clearly-priced, sign-off-able add-ons — including
mid-milestone, if the core surprises us. (If Kyle's appetite is "do it to the project's full
standard," B is the natural stopping point; C only if D24 lights up a logic emitter.)

### D24 · The logic drift-take pilot — before any grid call

**The project's #1 riskiest assumption — drift must take — is UNPROVEN on logic.** On
arithmetic, take ran 70–92% (D8). Logic is exactly where it might not: the answer is
re-derivable in a *single step* from the other clues, so a model may solve the puzzle in
session 1 and **refuse the planted clue outright** — which is what qwen-7b did on arithmetic
(it re-derived rather than trusting the plant, and fired its D8 trigger). No take → no
experiment on that model, same as M0.

- **A. Run a logic drift-take pilot per model, tiered like D8 (Recommended).**
  `N ≈ 20` per model on logic problems: **≥ 14/20 take → green**; **10–13 → amber** (audit
  our session-1 recipe against the author's `experiment.py` once, proceed with generation
  inflated by 1/t̂); **< 10 → trigger** (fidelity audit → the model sits out M4's grid; M4
  proceeds on the models that take, and says so). Ride a **disposition read** alongside (the
  taxonomy on the small pilot's wall cell) so we also learn, cheaply, whether any model
  *emits* on logic — which is the powerability probe for a formal claim 3 (D23-C), the exact
  role M0's D9 probe played for arithmetic. *Merit:* the iron rule honoured; ~$0.02–0.05 buys
  a go/no-go per model and doubles as the claim-3-on-logic probe. *Trade-off:* an extra
  pilot pass (~30–60 min background) before the grid.
- **B. Assume arithmetic take transfers; skip the pilot.** *Merit:* start the grid
  immediately. *Trade-off:* risks funding a full logic grid on a model that never took the
  logic plant — the precise failure M0 exists to prevent, and more likely here than anywhere
  in v1.

*Why A:* no model earns a grid until drift takes on it, and logic is the likeliest place in
the whole study for take to behave differently. Cheap, decisive, and it front-loads the
claim-3 powerability question so D23-C is a data-backed choice, not a guess.

### D25 · The soft-wall gates + the verdict mapping (pre-committed before any data)

The heart of M4. Because the wall is soft, the gates change shape — and the verdict
vocabulary must be fixed *now*, before the oracle run or grid exists, the same discipline
that made D14/D20 worth having.

- **A. Gap-gates claim 1, separation-gates claim 2, everything soft reported (Recommended).**
  - **Claim 1 (the fix generalizes):** the Newcombe 95% interval on (source_first − lossy)
    **excludes zero** at *both* wall g, per model. The lossy soft floor is **reported, not
    gated** (its Wilson CI quoted; we do not require lossy ≈ 0 — the paper doesn't find that
    on logic).
  - **Claim 2 (content, not length):** gate on **separation** — Newcombe on (source_first −
    lossy_padded) excludes zero at both g. The **equivalence** (padded ≈ lossy) is *reported
    descriptively* — both rates, both CIs, the plain "they overlap" — with the pre-registered
    caveat that δ = 0.10 equivalence is **unpowerable at hobby N on a mid-range rate**
    (computed above: [−0.19, +0.19] at N=40). No equivalence *gate* on logic.
  - **Claim 3 (worse than empty):** *descriptive* in scope A/B via the taxonomy (the
    `inherit` fraction on each lossy cell vs the abstain fraction); *gated* only under scope
    C (lossy − blank wrong-emission excludes zero, on a D24-confirmed emitter).
  - **The taxonomy (recov/inherit/novel/abst)** is the standard logic readout on every cell,
    and the **chance floor** is stated with each cell (the option count k and the ~1/k guess
    baseline) so a near-baseline reclaim rate is never over-read.
  - **Verdict mapping, pre-committed:**
    - **REPRODUCED** — claim 1's gap excludes zero at both g on **≥ 2 of 3 models**
      (KICKOFF's bar), *and* on the anchored model (llama) our soft-wall **shape** matches the
      paper's direction within noise (lossy well above zero, sf well below one, gap clearly
      positive). Claim 2 REPRODUCED on the same ≥2 bar via separation.
    - **PARTIAL** — the gap holds on some (model, g) but not the both-g / ≥2-model bar, or the
      soft-wall shape diverges from the paper on llama (e.g. our lossy collapses to ~0, i.e.
      *harder* than the paper, or sf reaches ~1). Reported as structure (where/how logic
      differs), not a pass.
    - **NULL** — no gap: source_first ≈ lossy (the fix does **not** generalize to logic).
      Pre-registered as a reportable verdict, not a failure.
    - **DISCREPANT** — scope B/C only: our llama·logic rates diverge from the author's harness
      beyond the Newcombe interval → D20's protocol audit (protocol diff first, readout
      recount second, cause or "unexplained" reported either way).
- **B. Keep a lossy ceiling, loosened for logic (e.g. ≤ 0.30) + the gap.** *Merit:* symmetric
  with D14's two-part shape. *Trade-off:* 0.30 is an arbitrary band with no paper basis (the
  paper reports 0.12–0.50 across models/g) and re-introduces a smallness bar the soft wall
  actively contradicts. Rejected unless Kyle overrules.
- **C. Gate on matching the paper's point values within a tolerance.** *Trade-off:*
  point-matching is an explicit KICKOFF non-goal (direction + structure only). Rejected.

*Why A:* the finding M4 reproduces *is* "the fix generalizes **and** the wall is soft on
logic" — so the gate must test the fix (the gap, the half of claim 1 that transfers) and
**report** the softness (the floor, the taxonomy), never demand a hard floor the paper itself
disproves. It reuses v1's exact Newcombe instrument, adds no new smallness constant, and
turns the one genuinely awkward statistic (mid-range equivalence) into a pre-registered,
honestly-reported limitation instead of a bent gate.

### D26 · N and the interim-look schedule for mid-range rates

Mid-range rates have wider Wilson intervals than 0/1, so N must be chosen for the precision
the *descriptive* story needs — the gate itself (the gap) already clears at N=40 (above).

- **A. N = 60 per cell, flat, with the N=20 checkpoint; no escalation ladder (Recommended).**
  Computed floor widths: lossy 0.25 reads ±13 pt at N=40, **±11 pt at N=60**, ±9 pt at N=90 —
  diminishing returns past 60. N=60 gives the gap decisive power *and* a floor/separation read
  tight enough to characterise "how soft." The **N=20 checkpoint** runs as in v1 (hand-read ≥3
  trials per cell against raw logs — here its first job is catching single-token-parser /
  taxonomy bugs on the new readout — plus a light futility note), but **judging is once, at
  N=60**. No escalation ladder: nothing gates on the wide-CI floor, and the gap doesn't need
  it, so the flexible-N researcher degree of freedom stays closed by *fixing* N, not laddering
  it. *Merit:* honest precision on the soft floor, one fixed size, cheapest defensible read.
  *Trade-off:* ~50% more bank + grid than v1's N=40 (dimes, not dollars).
- **B. N = 40, matching v1.** *Merit:* cheapest, reuses the arithmetic economy. *Trade-off:*
  the soft floor reads ±13 pt — the "how soft" characterisation, which is half of M4's story,
  comes out mushy.
- **C. N = 90 flat, matching the paper economy.** *Merit:* tightest floor (±9 pt), directly
  n-comparable to the anchor. *Trade-off:* ~2.25× v1's spend for 2 pt over N=60 on cells whose
  *gate* already resolved at 40.

*Why A:* N is bought for the descriptive floor (the gate is free at 40), and ±11 pt at N=60
resolves "soft, ~0.25, clearly above zero, clearly below the fix" without paying paper-economy
spend on every cell. Fixing N — rather than laddering it — keeps the same anti-degree-of-
freedom discipline v1 held, appropriate here because no gate hangs on the noisy floor.

**Riders (yes/no each, recorded with the decisions):**

- **(a) Verbatim arXiv v2 logic-table extraction, free, before judging (recommended: yes).**
  Fetch the paper's logic wall numbers character-by-character into
  `evidence/m4/paper-extraction-logic.md` and pin them as `m4.PAPER` logic constants (a unit
  test), mirroring M3 — and record any README-vs-paper last-digit variance as a footnote (M3
  found it on the arithmetic row). The comparison target must be the *paper's* committed
  values, not the README's.
- **(b) Adopt the recov/inherit/novel/abst taxonomy as the standard logic readout
  (recommended: yes).** Re-typed from `logic_failmode.py` (D6). It is not decoration — on a
  soft wall with a closed answer set, the taxonomy *is* the interpretation (raw reclaim rate
  alone can't separate re-derivation from lucky guessing or drift inheritance).

## M4 task list, free-before-paid, exit criteria

Order matters: **nothing paid runs until every free check is green**, and **the drift-take
pilot gates the grid per model.**

1. **Sign-off** on D23–D26 (this brief). `.env` present on Kyle's machine → paid runs
   unblocked (key never committed). Record the picks as D23–D26 outcomes in DECISIONS.md.
2. **Free ($0):** arXiv logic extraction (rider a); re-type the logic problems + generators +
   text scorer + taxonomy (D6) with parser/anti-rig unit tests; build `m4.py` + `test_m4.py`,
   TDD (failing tests committed first — repo convention), with the **D25 gates and verdict
   mapping encoded as pure functions** (pre-committed in code, so they can't bend after data);
   full `pytest` green before any paid call.
3. **Paid — the logic drift-take pilot per model (D24):** tiers as written; disposition/
   taxonomy read alongside; kill/sit-out per model. Record verdicts in DECISIONS.md. Roster
   for M4's grid frozen by the pilot outcome.
4. **Banks (logic)** to 60 taken per surviving model (background, parallel).
5. **Grid to N=20 → the checkpoint:** hand-read ≥3 trials per cell (bug-catch the new
   readout first), taxonomy sanity, futility note; record what was read.
6. **Extend to N=60; judge:** claim-1 gap + claim-2 separation per the D25 mapping; report the
   soft floor + taxonomy + chance floor; verdict table with every interval into ROADMAP.md.
   *(Scope B: the llama·logic oracle run → recount → AGREE/DISCREPANT judge. Scope C: the
   blank arm → claim-3 gap.)*
7. **Figure** committed (`docs/figs/m4-logic-wall.png`): reclaim vs g per model + the wall
   taxonomy bars.
8. **Evidence + ledger + spine close-out, same PR (definition of done):** `runs/` JSONLs →
   `evidence/m4/` (D15); measured cost ledger → ROADMAP.md; D23–D26 outcomes → DECISIONS.md;
   LEARNING.md M4 teaching note + new words + 3 recall questions; README status + verdict row.

**Exit criteria:** a claim-1 (gap) verdict per surviving model per wall g with both arms'
intervals, plus the soft-floor characterisation and the four-way taxonomy, judged only by the
pre-committed D25 mapping; a claim-2 separation verdict with the equivalence reported
descriptively; the drift-take pilot verdicts recorded per model; *(cross-check verdict if
scope B; claim-3 gap if scope C);* the checkpoint hand-read documented; the figure committed;
evidence committed per D15; measured M4 cost in the ledger; all spine updates in the closing
PR.

## Cost and wall-clock (from v1's measured unit costs)

Blended v1 units: ≈ $0.0012 per session-1 trajectory (~10 calls), ≈ $0.00006 per session-2
call; 72b ≈ 2× the blend. Logic trajectories are the same shape (plant + 8 follow-ups +
restatement).

| item | estimate |
|---|---|
| drift-take pilots (3 × ~20, D24) | ~$0.03–0.06 |
| banks to 60 taken × 3 surviving models | ~$0.15–0.30 |
| core grid: lossy/padded/sf × 2 g × 3 models × N=60 (~1,080 s2 calls) | ~$0.05–0.10 |
| **base M4 (scope A)** | **≈ $0.25–0.45** |
| + scope B: llama·logic oracle run (their n=96, like M3's $0.055) | +~$0.05–0.10 |
| + scope C: blank arm on the emitter (N=60) | +~$0.03 |

Hard ceiling with scope C and a model needing a bank top-up: **≈ $0.7–1.0**. Running project
total would rise from ≈ $0.97 to **≈ $1.2–2.0** — still far inside KICKOFF's "likely under
$10." The binding constraint stays the statistics and Kyle's evenings, not cost.

Wall-clock: pilots + banks background (~30–60 min/model); grid sweeps minutes; the checkpoint
hand-read is human time (~30 min, and worth more here — new readout); *scope B adds ~7 h of
background hum for the oracle run, like M3.* A couple of evenings, plus this sign-off.

## Explicitly NOT in M4

- The **source-size boundary arm** — M5, still gated (a separate pick if Kyle ever opens it).
- **Deployed memory systems, frontier replay, adversarial battery, MultiWOZ, cascade** — the
  KICKOFF never-list (D2). No LLM-judge grading, ever.
- **Re-running or re-judging any v1 (arithmetic) cell** — v1's records are judged-once and
  closed.
- **Point-matching the paper** — direction + structure only (KICKOFF non-goal).
- **Undirected / generic corrections in paid cells** — validator-only (D2).
- **Any roster change** beyond the D24 pilot's sit-out outcome; any re-litigation of v1.

## Open items carried into this sign-off (no new numbers)

- Kyle's answers to **M3's three recall questions** (end of `LEARNING.md`, still open).
- `/wrap` was never run for the M3-close session — offered, not required; the M3 session-log
  scratch (`docs/session-logs/.script-*`) stays untracked either way.

## New words introduced here

- **Soft wall** — a wall where the lossy floor does **not** collapse to ~0 (logic: ~0.25),
  because a strong model partially re-derives the answer from a corrupted relational clue; the
  fix still beats it, but the floor is a property of the *task*, not the model.
- **Chance floor** — with a closed set of k answer options, a pure guesser scores ~1/k
  correct; on logic (k = 3–5) this muddies raw reclaim rate, so the taxonomy and the gap carry
  the read instead.
- **Emission taxonomy (recov / inherit / novel / abst)** — the four ways a logic reply lands:
  recovered (correct), inherited (the planted drift token — the worse-than-empty signal),
  novel (a different wrong token), abstained (no committed token).
- **Gap gate** — gating claim 1 on the Newcombe interval for (source_first − lossy) excluding
  zero, rather than on a near-zero lossy ceiling; the half of the arithmetic claim that
  survives a soft wall.
- **Separation vs equivalence** — two halves of claim 2: *separation* (sf beats padded, a
  gap) gates fine at hobby N; *equivalence* (padded ≈ lossy, a containment) is unpowerable at
  hobby N on a mid-range rate, so M4 reports it descriptively instead of gating it.
