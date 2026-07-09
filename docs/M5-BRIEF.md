# M5 Start-of-Stage Brief — the source-size boundary arm (where the fix fails)

*Written 2026-07-09 · status: **awaiting sign-off** — D27–D30 proposed below; no M5 code
and no paid call until Kyle signs · scope source of truth: `docs/KICKOFF.md` (Milestone 5,
gated) · format follows `docs/M4-BRIEF.md`.*

## What M5 is, in plain terms

Every milestone so far has measured the brittle-memory effect where it **holds**: the wall
is real (M1), it's about content not length (M2), an independent build agrees (M3), and it
survives a change of task (M4, on deepseek). M5 is the mirror image — **the falsification
stage**. It goes looking for the place where the *fix itself* stops working.

The fix is **source_first**: at a tight memory budget, keep the recomputable *source* (the
receipt's line items — the material you'd need to redo the sum) and drop the re-derivable
*conclusion* (the wrong total). Across v1 this fix reclaimed ~1.00 while plain lossy sat at
~0.00 — the whole headline. But that fix has an unstated precondition: **the source has to
fit in the budget.** A two-item receipt's line items are short; they always fit. Grow the
receipt — more items, a longer source — against a *fixed* budget, and eventually the source
itself no longer fits. Past that point source_first has to shed line items too, and a
directed correction has nothing complete to recompute from. The prediction: **source_first
cliffs** — its reclaim rate falls off, back toward the lossy floor — precisely where a
source-first note runs out of room for the source.

That's the finding M5 reproduces: *the fix is bounded, and the boundary is the source-to-
budget ratio.* If we find the cliff, we've measured where the paper's remedy breaks. If we
*don't* — source_first stays high no matter how we starve it in our range — that's an
honest NULL, and a slightly better-news story than the paper tells (the remedy is sturdier
than its own boundary section implies). Both are reportable; neither is a failure.

**The honesty that has to lead this brief: the anchor is thin.** For M1–M4 the paper gave
us hard target numbers (the wall table, the logic table) to sit our results beside. The
paper's *boundary* discussion is qualitative and short, and — as of this writing — the
author's released code has **no source-size sweep at all** (its only boundary mechanism is a
*distance* sweep, `run_problem_distance`: pushing the error behind filler, a recency effect,
not a source-size one — see "The paper's boundary anchor" below). So M5 is, honestly, **our
clean operationalization of a claim the paper mostly states in prose.** That is still
legitimate reproduce-and-measure work — but it changes what the gate is allowed to test.
With no firm target number, M5 gates the **existence and direction** of the cliff (is there
a monotone, statistically separated drop as we starve the source?), and **reports** where it
sits — it never gates on a boundary *location* the paper doesn't firmly give. Every decision
below is built to be robust to the thin anchor; the first free step (the extraction rider)
is to pin down exactly how thin it is.

## The paper's boundary anchor (the target, and how thin it is)

What we can say before the extraction rider runs (D30 rider a fetches the paper's own words
verbatim and records precisely what's there):

- **v1/M4 had released-code anchors; M5 does not.** The released `experiment.py` carries
  three sweeps: the cross-session **integrity** sweep (the g-knob — v1's whole grid), a
  **depth** sweep (how many turns the drift commits over), and a **distance** sweep
  (`run_problem_distance` / `DISTANCES = (0, 4, 8, 16)`: fix the commitment, then push the
  planted error back behind unrelated filler so the model's grip on it dilutes). **None of
  these varies source size.** The `memory_note` source_first template keeps the *entire*
  `facts` string at every integrity — it never partially sheds line items — so the released
  code cannot cliff source_first by starving the source. The mechanism M5 needs doesn't
  exist in their harness; we build it.
- **So the comparison target is qualitative, not numeric.** The extraction rider will record
  whatever the paper's boundary paragraph actually claims (a direction, maybe a hand-wave at
  "large sources," possibly a figure) into `evidence/m5/paper-extraction-boundary.md`, and —
  critically — will state plainly if there is **no committed number to anchor against**. That
  absence is itself the finding that sets M5's gates: direction-and-existence, not location.
- **This is not a cross-check milestone.** M3's AGREE already validated our build against the
  author's harness on the arithmetic wall. M5 has **no oracle overlap cell** (their code has
  no source-size sweep to run), so there is **no DISCREPANT verdict** here — the honesty line
  is the extraction rider's candid record of the anchor's thinness, carried in the README.

## The crux: "source size" is really the source-to-budget ratio

The variable that makes source_first cliff is not source size in the abstract — it's **how
much of the recomputable source survives the note's character budget.** Call that the
**retained-source fraction** `s`: the fraction of the receipt's line items that fit into the
source_first note before it hits the budget. `s = 1.0` means the whole source survives (the
fix has everything it needs); `s = 0` means none of it does (the fix is starved down to the
wall). The cliff is source_first's reclaim rate plotted against `s`.

There are two knobs that move `s`, and choosing between them is D28:

- **Shrink the budget against a fixed receipt** (the recommendation). Fix the problem at a
  moderately large receipt — say **K = 6 line items** — and sweep the note's character budget
  down. source_first keeps as many *whole* line items as the budget allows (in listed order),
  so `s` steps `1.0 → 0.67 → 0.33 → 0.0` as the budget tightens to fit `6 → 4 → 2 → 0` items.
  The receipt (and its correct total, and the model's committed drift) is **held constant**;
  only the budget moves. This is literally "source_first cliffs past *its budget*," and it
  reuses v1's exact one-bank/paired-notes structure (the budget is a note-write-time knob,
  just like g was) — one bank of taken K = 6 trajectories, every sweep cell a write-time
  transformation of the same trajectory (D5 pairing across the whole sweep).
- **Grow the receipt against a fixed budget** (the alternative). Keep the budget fixed and
  add line items (K = 2, 4, 6, 8…). This is the more literal reading of "source-*size* sweep"
  — the source genuinely grows — but it has two costs: it needs a **fresh bank at every K**
  (the knob is now a problem property, not a note transformation, so no single paired bank),
  and — the real problem — **growing K also makes the model's own arithmetic harder** (a
  six-subtotal sum is harder to get right than a two-subtotal one, *even with the full source
  in hand*), which **confounds** budget-starvation with problem-difficulty. On a thin anchor
  we cannot afford a confounded cliff.

A worked example makes the recommended mechanism concrete. Our arithmetic `facts` string
today is a two-item receipt: `"mugs at $4 each (7 bought) and plates at $3 each (5 bought)"`.
A K = 6 receipt extends it to six `"<good> at $<p> each (<q> bought)"` clauses. The
source_first note carries as many whole clauses as fit the budget:

| budget fits | retained source `s` | source_first note carries | expected reclaim |
|---|:--:|---|:--:|
| 6 items | 1.00 | all six line items → full recompute possible | ~1.00 (the fix works) |
| 4 items | 0.67 | four line items, two subtotals missing | mid — the cliff edge |
| 2 items | 0.33 | two line items, four subtotals missing | low |
| 0 items | 0.00 | no line items — source fully gone | ~0 (starved to the wall) |

lossy is flat across all four: it carries only the tiny wrong conclusion (`"You concluded the
total was $X"`), which always fits, and always reclaims ~0 (the wall). The **cliff is the
source_first curve falling** as `s` drops; the **floor is lossy's flat line**. Arithmetic is
the right family for reading this cleanly: the answer is an *open number*, so there's **no
closed-set guess floor** to muddy the reclaim rate (the exact problem that forced M4's
four-way taxonomy). A source-starved model either recomputes correctly (rare, without the
items) or doesn't — the reclaim rate says what it means, no taxonomy required.

**One mechanical consequence to flag now (it becomes a build task, not a decision):** the
per-trial source gate must generalize. Today `source_present` is *binary* — does the first
18 characters of the facts string appear in the note? M5 needs a **graded** gate that counts
*how many* of the K line items survive in the note, so every trial can verify its own `s`
mechanically (a source_first note claiming `s = 0.67` must demonstrably carry four line
items and lack the other two; a lossy note must carry zero). That graded gate is a pure
function, unit-tested and anti-rig-checked before any paid call — same discipline as v1's
binary gate, one measurement richer.

## What v1 and M4 settled that M5 stands on (not re-litigated)

- **Arithmetic drift already takes on deepseek — decisively.** M4 needed a full drift-take
  pilot (D24) because take on *logic* was unproven and turned out fragile (llama sat out).
  M5 is arithmetic, where v1 measured deepseek at **20/20 take** (M0, post parser-fix) and
  banked **90/98** (M1). So M5 does **not** need a separate pilot decision — the riskiest
  assumption is already GREEN on this model and family. The one genuinely new wrinkle is the
  *multi-item* receipt (K = 6, not 2); the bank step below carries a lightweight take-sanity
  read on the new problem shape, and if take craters on big receipts that's a signal caught
  before any grid spend (the M0 kill-trigger philosophy, applied for free).
- **Roster is frozen (D13); M5 picks exactly one of the three, changes nothing.** No swaps,
  no new models.
- **Sampling (D10): temperature 0.0, max_tokens 600.** The M5 driver imports the constants
  from `m0.py`/`m1.py`, never redefines them.
- **The strict ANSWER-line parser and the format-explicit take-probe (D11) are reused as-is.**
  Arithmetic's `TAKE_PROBE` is already format-explicit; M5's readout is v1's exact reclaim
  readout (`grader.reclaimed`), no new parser. This is a deliberate contrast with M4, where a
  brand-new single-token logic readout hid a real bug — M5 leans on the readout v1 already
  hardened, so the new mechanical surface is the *note builder + graded gate*, not the parser.
- **Stats (D4): Wilson on cells, Newcombe on differences decide; bootstrap is robustness only.**
  The `bootstrap.py` appendix (D21) extends to M5's gated drop for free.
- **Evidence survives the machine (D15):** M5's paid JSONLs get committed to `evidence/m5/` in
  the closing PR; `uv.lock` and session-log text stay tracked.
- **The M0/M4 scoring lesson binds the new note builder.** Two live scoring bugs in v1 and one
  take-probe format bug in M4 all sailed through the deterministic fake and were caught only by
  the mandatory **N=20 checkpoint hand-read**. M5's new mechanical surface (budget-truncated
  source_first notes + the graded gate) is exactly where the next such bug hides — so the N=20
  checkpoint hand-read is **mandatory**, and its first job here is verifying that the truncation
  and the graded `s` measurement read correctly on real replies before any cell scales.
- **D6 — the author's code is a protocol reference, re-typed with attribution, never imported.**
  M5 re-reads `experiment.py`'s boundary sweeps for fidelity and re-types nothing new that
  isn't ours (the budget-truncation mechanism is our construction, since theirs has none);
  `reclaim-eval` never enters `pyproject.toml`.
- **Not re-litigated:** v1's and M4's verdicts, D1–D26, the v1 scope. Settled. M5 re-runs and
  re-judges nothing prior.

## The design: one bank, a budget sweep, one figure

Everything M5 needs is a *budget-swept* sibling of machinery v1 already has:

- **Problems (a small generator extension):** generalize the arithmetic `generate()` from a
  fixed two-item receipt to a **K-item receipt** (K = 6 recommended, per D28), one subtotal
  corrupted exactly as today (`wrong_premise` / `drift` / `locus` unchanged in shape), the
  `facts` string listing all K line items. Validated by construction and re-proved
  independently (the existing `validate()` pattern, extended to K items). Registered on a
  fresh `m5-` problem schedule.
- **The note builder extends to a budget cap (`notes.py`):** source_first keeps whole line
  items in listed order up to a character budget `B`, dropping the overflow; lossy is
  unchanged (tiny conclusion, always fits). The four sweep cells are the four budgets `B`
  chosen so `s` lands on `{1.0, 0.67, 0.33, 0.0}` for a K = 6 receipt. The graded per-trial
  source gate (`retained_fraction`) runs on **every** trial: a cell claiming `s` must carry
  exactly that many line items, mechanically verified before it counts.
- **The bank (one, fixed-K):** a pool of *taken* K = 6 arithmetic trajectories on deepseek —
  session-1 conversations where the model committed to the planted drift total — on a fresh
  `m5-` schedule. Because the budget is a note-write-time knob (D28-A), **one bank feeds every
  sweep cell** (D5 pairing across the whole sweep, exactly v1's structure).
- **The grid + figure:** session 2 = `[system, note, directed correction]`, one call per
  trial, note gated per trial (graded `s` verified), reply scored by the strict reclaim
  parser. Two arms (lossy floor + source_first cliff) × four budget points × N (D29). The
  figure (`docs/figs/m5-boundary.png`): **source_first reclaim vs retained-source fraction `s`**
  — the cliff curve — with the flat lossy floor as a reference line, Wilson bars, per-point N.
  (`make_figure`'s sub-roster/one-model handling from `m4.py` is reused for the single-model
  figure.)

## Decisions — D27–D30 (pick or veto; recommendation marked; numbering continues DECISIONS.md)

### D27 · The one model + family + the arm set

M5 is a one-model milestone by KICKOFF's gated scope. The choice is which model and family
read the cliff cleanest, and how many arms to run.

- **A. deepseek · arithmetic · lean two-arm core {lossy, source_first} (Recommended).**
  deepseek is the roster's clean answerer: it reclaimed source_first **40/40 (1.00)** on the
  two-item arithmetic wall (v1), so it starts at the ceiling with **maximal headroom to fall**
  — a cliff is unambiguous. It's terse (it emits a clean ANSWER line and stops), which matters
  because the alternative confound here is *token-cap rambling*: M2 caught llama rambling into
  its 600-token cap on hard cells and abstaining (mis-read as non-reclaim). A multi-item
  recompute is long; a rambler would hit that cap and produce a *fake* cliff (abstains, not
  budget-starvation). deepseek dodges it. Arithmetic is the hard, clean wall (open-number
  answer, no guess floor), so the cliff reads in raw reclaim rate with no taxonomy. The lean
  two-arm core (lossy = the flat floor reference, source_first = the arm that cliffs) is the
  thinnest honest test of "the fix is bounded." *Trade-off:* no length-control arm (see the
  layerable add-on below); deepseek has no published logic/boundary number, but neither does
  any model here (the anchor is thin for everyone).
- **B. deepseek · arithmetic · core + a lossy_padded length-control arm.** Add lossy_padded
  (lossy padded up to the budget `B`) at each sweep point, so a note *the same length as*
  source_first but carrying no source stays flat at the floor — re-demonstrating "content, not
  length" (claim 2) at every rung of the cliff and ruling out any residual length artifact.
  *Merit:* the strongest confound control on a thin-anchor milestone. *Trade-off:* +4 cells of
  spend (dimes on one model) before the headline cliff has read once — against the lean-first
  guardrail. Layer it if the core reads clean and Kyle wants the airtight version.
- **C. llama · arithmetic.** llama is the paper's primary model (the natural anchor elsewhere),
  but it is the *worst* pick here: its 600-token-cap rambling (documented in M2's knob dip)
  would confound the source-size cliff with a token-budget cliff — the one artifact M5 most
  needs to avoid. Rejected unless Kyle wants the paper's model despite the confound.

*Why A:* the cliff reads cleanest on the model that starts at 1.00, answers tersely, and
carries no guess floor — deepseek on arithmetic on all three counts. B (the padded control)
and C's ambitions are real but layerable; the lean two-arm core is M5's honest headline, and
the padded arm is a clearly-priced add-on exactly as M4's cross-check/claim-3 arms were.

### D28 · The sweep axis + the cliff mechanism

The M5-specific crux: what "source size" varies, how the budget binds, and where the sweep
points sit. (Mechanism worked through in "The crux" above.)

- **A. Fix the receipt at K = 6, sweep the note budget; report against retained-source
  fraction `s ∈ {1.0, 0.67, 0.33, 0.0}` (Recommended).** source_first keeps whole line items
  in listed order up to budget `B`; the four budgets are chosen to fit `6 / 4 / 2 / 0` items.
  The problem is held constant; only the budget moves, so the cliff is attributable to the
  source-to-budget ratio and nothing else. **One bank** (taken K = 6 trajectories) feeds every
  cell as a write-time note transformation (D5 pairing across the sweep — v1's exact
  structure). *Merit:* literally "past its budget"; cleanest confound control (same problems,
  same trajectories, only the budget differs); reuses the harness's one-trajectory-many-notes
  spine; cheapest (one bank). *Trade-off:* re-reads "source-*size* boundary" as "source-to-
  *budget* ratio" (held source, shrunk budget) — a defensible operationalization that the
  brief and the README must state plainly.
- **B. Fix the budget, grow the receipt (K = 2, 4, 6, 8); report against K.** The literal
  "source-size sweep" — the source genuinely grows. *Merit:* matches the KICKOFF phrase most
  directly. *Trade-off:* needs a **fresh bank at every K** (no single paired bank), and —
  decisively — growing K makes the model's own arithmetic harder even with the full source, so
  a cliff **confounds** budget-starvation with problem-difficulty. Rejected as the primary axis
  for that confound; a single high-K spot-check could ride along descriptively if Kyle wants a
  literal-size data point.
- **C. Vary a source-retained fraction directly (keep fraction f of items), no explicit char
  budget.** Closest to generalizing the author's `integrity` knob, but "budget" becomes an
  abstract fraction rather than a real character cap — it loses the concrete "the note ran out
  of room" mechanism that is the whole point. Rejected as less faithful than A.

*Why A:* holding the problem fixed and shrinking the budget is the only axis that isolates the
budget-starvation mechanism from problem-difficulty, keeps a single paired bank, and matches
"past its budget" literally. The re-reading of "size" as "ratio" is the honest cost, stated
up front; B's literal size-growth is available as a descriptive spot-check without letting its
confound touch the gate.

### D29 · What defines the cliff — the boundary gate + the verdict mapping (pre-committed before any data)

The heart of M5. Because the anchor is thin (no committed boundary number), the gate tests
the cliff's **existence and direction**, never its *location* — and the verdict vocabulary is
fixed **now**, before any note builder or paid cell exists, the same discipline that made
D14/D20/D25 worth having.

- **A. Gate existence-and-direction; report the location and the floor (Recommended).**
  - **The cliff (the gate):** three conditions, all pre-committed. **(i) Ceiling intact at full
    source** — source_first reclaim at `s = 1.0` is high (its Wilson 95% *lower* bound clears
    0.80; deepseek should read ~1.00). Without this there is no fix to break, and the milestone
    is inconclusive, not a cliff. **(ii) A real drop** — the Newcombe 95% interval on
    `RR(s=1.0) − RR(s=0.0)` **excludes zero** (source_first genuinely falls as the source is
    starved). **(iii) Monotone within noise** — reclaim is non-increasing across
    `s = 1.0 → 0.67 → 0.33 → 0.0`, each step's Newcombe interval not *rising* beyond noise (a
    clean cliff falls, it doesn't bounce).
  - **The boundary location — reported, not gated.** The `s*` where source_first first drops
    below a reference level (its own `s = 1.0` cell, and the 0.5 mark) is quoted with its
    Wilson CI, **descriptively** — the paper gives no number to gate against, so we report
    where our cliff sits and let the reader see it.
  - **The floor — reported.** lossy's reclaim across all four `s` (expected flat at ~0) is
    quoted with Wilson CIs, as the wall reference the cliff falls toward.
  - **The confound watch (checkpoint's job).** The N=20 hand-read verifies the source_first
    drop is *genuine recompute-failure* (the model tries and can't, for lack of items), not
    token-cap abstains or a truncation/gate bug. A drop that the checkpoint traces to an
    artifact is PARTIAL, not REPRODUCED — the M4 confound lesson, pre-committed.
  - **Verdict mapping, pre-committed:**
    - **REPRODUCED** — all three cliff conditions hold (ceiling intact, drop excludes zero,
      monotone within noise) **and** the checkpoint confirms genuine recompute-failure, with
      lossy flat at its floor. The fix is bounded: source_first fails as the source outgrows
      the budget, exactly as predicted.
    - **PARTIAL** — source_first degrades but the full→starved drop doesn't clear the Newcombe
      separation (a shallow or underpowered cliff), **or** the decline is non-monotone, **or**
      the checkpoint attributes the drop to a confound (token-cap abstains, a truncation/gate
      bug) rather than budget-starvation. Reported as structure (how far it bends, and why),
      not a pass.
    - **NULL** — no cliff: source_first stays high (its Wilson lower bound holds above, say,
      0.5) across the whole budget sweep. Pre-registered as a **reportable** verdict — the fix
      is more robust to source-starvation than the paper's thin boundary implied, an honest and
      slightly better-news result, not a failure.
    - **(No DISCREPANT.)** M5 has no oracle overlap cell (the released harness has no
      source-size sweep), so there is no cross-check verdict. The anchor's thinness is carried
      as the extraction rider's candid record, in the README, beside the verdict.
- **B. Gate on the cliff reaching the lossy floor (source_first at `s=0` ≈ lossy).** *Merit:*
  a crisp "the fix fully collapses." *Trade-off:* too strong — a real but *partial* cliff
  (source_first falls to 0.4, well below its ceiling but above the lossy 0.0) is exactly the
  interesting boundary finding, and this gate would miss it. Rejected.
- **C. Gate on matching a paper boundary location within a tolerance.** *Trade-off:* there is
  no committed location to match, and point-matching is an explicit KICKOFF non-goal. Rejected.

*Why A:* on a thin anchor the defensible thing to test is that the effect *exists and points
the predicted way* — a monotone, statistically separated decline in source_first as the source
is starved — while **reporting** the location the paper never pins. It reuses v1's exact
Newcombe/Wilson instruments, adds no new smallness constant beyond the one "ceiling intact"
lower bound, and turns the anchor's weakness into a pre-registered reporting stance instead of
a bent gate. The confound watch is promoted to a first-class gate condition because M4 proved
a real-looking drop can be an artifact.

### D30 · N per cell, the checkpoint, and the free riders

The cliff's *edge* cells (`s = 0.67, 0.33`) are mid-range by design — that's where the drop
happens — so N is chosen for the precision the descriptive cliff-shape needs, exactly M4's
logic. The top/bottom cells are near 0/1 (tight at any N); the transition cells are the ones
that need width.

- **A. N = 60 per cell, flat, with the N=20 checkpoint; no escalation ladder (Recommended).**
  Mirrors M4's D26 reasoning: a mid-range cell reads ±13 pt at N=40, **±11 pt at N=60**, ±9 pt
  at N=90 — diminishing returns past 60. The gate itself (the full→starved Newcombe drop) is
  decisive well before 60; N buys a **transition tight enough to see the cliff's shape** rather
  than a mush. The **N=20 checkpoint** runs as always (hand-read ≥3 trials per cell against raw
  logs — here its first jobs are verifying the budget-truncation and the graded-`s` gate on real
  notes, and watching for the token-cap confound — plus a light futility note), but **judging is
  once, at N=60**. No escalation ladder: nothing gates on the noisy transition floor, so fixing
  N keeps the anti-degree-of-freedom discipline closed. Eight cells (2 arms × 4 `s`) × N=60 on
  one model, all from one bank — the cheapest defensible read. *Trade-off:* ~50% more grid than
  N=40 (pennies on one model).
- **B. N = 40 (v1's arithmetic economy).** *Merit:* cheapest, reuses v1's number. *Trade-off:*
  the transition cells read ±13 pt — the cliff's *shape*, which is half of M5's story, comes
  out mushy.
- **C. N = 90 (paper economy).** *Merit:* tightest transition (±9 pt). *Trade-off:* ~2.25× the
  spend for 2 pt over N=60 on a milestone whose gate resolves far below 60.

*Why A:* N is bought for the descriptive cliff-shape (the gate is free well under 40), and
±11 pt at N=60 resolves "where and how steeply source_first falls" without paying paper economy
on every cell. Fixing N rather than laddering it holds the same discipline v1 and M4 held.

**Riders (yes/no each, recorded with the decisions):**

- **(a) The verbatim paper-boundary extraction, free, before judging (recommended: yes).**
  Fetch the paper's boundary/source-size paragraph character-by-character into
  `evidence/m5/paper-extraction-boundary.md`, mirroring M3/M4's extraction. Its **first job is
  to establish how thin the anchor is** — whether the paper gives any committed number, a
  figure, or only a qualitative direction — and to record that plainly. If a number exists it's
  pinned as an `m5.PAPER` constant (a unit test) and reported beside our cliff *descriptively*
  (never as a gate, per D29). If none exists, that absence is the recorded finding that
  justifies D29's existence-and-direction gate.
- **(b) A fidelity note on the mechanism's provenance (recommended: yes).** Record, in the same
  extraction file, that the budget-truncation source-size mechanism is **our construction** —
  the released `experiment.py` has no source-size sweep (only integrity, depth, and *distance*)
  — with the exact citation of what their boundary code *does* do, so a reader can see precisely
  where M5 reproduces the paper's *claim* versus where it operationalizes it with our own
  instrument. This is the D6 attribution discipline applied to an arm the author didn't ship.

## M5 task list, free-before-paid, exit criteria

Order matters: **nothing paid runs until every free check is green.**

1. **Sign-off** on D27–D30 (this brief). `.env` present on Kyle's machine → paid runs
   unblocked (key never committed). Record the picks as D27–D30 outcomes in DECISIONS.md.
2. **Free ($0):** the paper-boundary extraction (rider a) + the fidelity note (rider b); extend
   the arithmetic generator to K-item receipts and the note builder to a budget cap, with the
   **graded per-trial source gate** (`retained_fraction`) as a pure function; build `m5.py` +
   `test_m5.py`, TDD (failing tests committed first — repo convention), with the **D29 cliff
   gate and verdict mapping encoded as pure functions** (pre-committed in code, so they can't
   bend after data); the anti-rig validator suite extended to the graded gate (a fake that
   "reclaims" only when the required line items are present); full `pytest` green before any
   paid call.
3. **Bank (one, fixed-K):** to N=60 taken K = 6 deepseek trajectories on a fresh `m5-` schedule
   (background), carrying a lightweight take-sanity read on the multi-item shape — if take
   craters on big receipts, stop and look before the grid.
4. **Grid to N=20 → the checkpoint:** hand-read ≥3 trials per cell — verify budget-truncation
   and the graded `s` gate on real notes first, watch for the token-cap confound, futility note;
   record what was read.
5. **Extend to N=60; judge:** the D29 cliff gate (ceiling intact, drop excludes zero, monotone,
   confound-clean) + the verdict mapping; report the boundary location and the lossy floor
   descriptively; verdict + every interval into ROADMAP.md.
6. **Figure** committed (`docs/figs/m5-boundary.png`): source_first reclaim vs `s` (the cliff),
   lossy floor reference line, Wilson bars, per-point N.
7. **Evidence + ledger + spine close-out, same PR (definition of done):** `runs/` JSONLs →
   `evidence/m5/` (D15); measured cost ledger → ROADMAP.md; D27–D30 outcomes → DECISIONS.md;
   LEARNING.md M5 teaching note + new words + 3 recall questions; README status + verdict row.

**Exit criteria:** a cliff verdict (REPRODUCED / PARTIAL / NULL) judged only by the
pre-committed D29 mapping, with the source_first curve and lossy floor across all four `s` and
the full→starved Newcombe drop recorded; the boundary location reported descriptively; the
extraction rider's candid anchor-thinness record committed; the checkpoint hand-read (including
the confound watch) documented; the figure committed; evidence committed per D15; measured M5
cost in the ledger; all spine updates in the closing PR.

## Cost and wall-clock (from v1/M4's measured unit costs)

Blended units: ≈ $0.0012 per session-1 trajectory (~10 calls), ≈ $0.00006 per session-2 call.
M5 is one model (deepseek, the cheaper blend), one bank, a note-transformation sweep.

| item | estimate |
|---|---|
| bank to 60 taken K = 6 (deepseek, ~0.9 take → ~67 trials) | ~$0.08 |
| grid: {lossy, source_first} × 4 `s` × N=60 (~480 s2 calls) | ~$0.03 |
| **base M5 (D27-A core)** | **≈ $0.10–0.15** |
| + D27-B: lossy_padded length-control arm (4 cells × N=60) | +~$0.02 |
| + D28-B: a single high-K descriptive spot-check bank | +~$0.05–0.08 |

Hard ceiling with the padded arm and a bank top-up: **≈ $0.25**. Running project total would
rise from ≈ $1.40 to **≈ $1.5–1.65** — far inside KICKOFF's "likely under $10." As always,
the binding constraint is the statistics and Kyle's evenings, not cost.

Wall-clock: the bank is background (~30–45 min); the grid sweeps in minutes (all from one
bank); the checkpoint hand-read is human time (~30 min, and load-bearing here — a new note
builder). One evening, plus this sign-off.

## Explicitly NOT in M5

- **A logic-family boundary** — M5 is arithmetic only (the clean wall; logic's directed
  correction is confounded on ordering puzzles, M4's finding). No new task family.
- **A distance/recency sweep** — the author's `run_problem_distance` is a *different* boundary
  (error pushed behind filler), not source size. Out of M5's scope; named only to keep the
  anchor honest.
- **Deployed memory systems, frontier replay, adversarial battery, MultiWOZ, cascade** — the
  KICKOFF never-list (D2). No LLM-judge grading, ever.
- **Re-running or re-judging any v1 or M4 cell** — their records are judged-once and closed.
- **Point-matching the paper** — direction + structure only (KICKOFF non-goal), and doubly so
  here where the paper commits no boundary number.
- **Any roster change** — M5 picks one frozen-roster model; no swaps.
- **A second model** unless Kyle explicitly layers one — M5 is one-model by gated scope.

## Open items carried into this sign-off (no new numbers)

- Kyle's answers to **M3's and M4's three recall questions** (end of `LEARNING.md`, still open).
- `/wrap` was never run for the M3-close or M4-close sessions — offered, not required; the
  session-log scratch (`docs/session-logs/.script-*`) stays untracked either way.

## New words introduced here

- **Retained-source fraction (`s`)** — the fraction of a problem's recomputable source (its
  line items) that survives the note's character budget; M5's sweep axis. `s = 1.0` the whole
  source fits, `s = 0` none of it does. The cliff is source_first's reclaim rate vs `s`.
- **The cliff** — the drop in source_first's reclaim rate as `s` falls: the fix works while the
  source fits the budget and fails once it doesn't. M5's headline.
- **Falsification stage** — a milestone that goes looking for where a reproduced effect
  *breaks* rather than where it holds; M5 measures the boundary of the fix, the one place a
  clean NULL is a genuine, better-news outcome.
- **Thin anchor** — a paper claim stated qualitatively (or with no released code) rather than
  as a committed number to compare against; it forces a gate on the effect's *existence and
  direction* rather than its *location* (D29), and an honest record of the thinness (rider a).
- **Graded source gate** — the per-trial mechanical test generalized from binary present/absent
  (v1's `source_present`) to *counting* how many line items survive in a note, so every trial
  can verify its own `s`.
