# M2 Start-of-Stage Brief — the controls

*Written 2026-07-07 · status: **signed 2026-07-07** — D16-A, D17-A (rider a: no), and
D18-A picked by Kyle and recorded in `DECISIONS.md`; claim 2's
equivalence margin δ is NOT among them (it was committed as **D7** at the M0 sign-off,
before the project's first paid call — restated below, not re-opened); no M2 code and no
paid call until Kyle signs · scope source of truth: `docs/KICKOFF.md` (Milestone 2) ·
format follows `docs/M1-BRIEF.md`.*

## What M2 is, in plain terms

M1 measured the wall: at wall integrity a lossy note pins reclaim at ~0 while a
source-first note reclaims essentially always — claim 1 CLEARED, 3 of 3 models. M2 runs
**the controls that make that claim mean what it says**, plus the cells that complete
the figure:

1. **Content, not length (claim 2).** At the wall, a source_first note is *longer* than
   a lossy note (the facts survive). A skeptic can say: "maybe the correction worked
   because the note gave the model more text, not because the text was the source."
   The **lossy_padded** policy kills that objection: the same lossy note, padded with a
   fixed, explicitly content-free filler sentence until it is at least as long as the
   source_first note at that g — same character budget, different content. If padding
   doesn't rescue reclaim (equivalent to plain lossy within the pre-committed ±0.10)
   while source_first still beats it, then what the characters *say* is the wall, not
   how many there are.
2. **Worse than empty (claim 3 — the title claim).** Holding a blank memory ("no
   figures were retained"), a model should say it can't recompute and decline. Holding
   a lossy note, the paper says it confidently re-asserts a wrong number instead — the
   lossy note is *worse than nothing*, because it converts silence into confident
   error. M0's 12-trial probe saw this at full strength on deepseek (11/12 wrong
   emissions vs 0/12 blank, post-parser-fix); M2 measures it at the pre-registered
   N≈40 under the gate. deepseek is the roster's only emitter — llama and qwen72b
   abstain at the wall (their probe NULLs are settled verdicts, D9/D13), and KICKOFF
   pre-commits reporting those nulls plainly.
3. **The knob fills (descriptive).** Fill g = 0.6 and 1.0 for lossy and source_first so
   the committed figure shows the whole curve of reclaim rate vs note integrity: both
   policies at the ceiling while the source survives (g ≥ 0.5 keeps it, by the
   threshold mapping), and the lossy curve falling off the cliff below 0.5. These cells
   decide no claim — they are **descriptive** (measured and plotted with Wilson bars,
   gating nothing), unlike the **gated** cells above whose intervals decide verdicts.

Everything M2 needs already exists in code: all four note policies have been pure
functions in `notes.py` since M0 (the padded builder and the blank template included),
`runner.verify_note_gate` checks every note in the right direction before a trial
spends a token, the g ≥ 0.99 lossy special case (the full session-1 transcript instead
of a note — theirs verbatim) is in `runner.session2_base`, and claim 3's counting rule
(`grader.emitted_wrong`) has been in the grader with unit tests since M0. So M2 is:
build a small grid driver over M1's banks, run seven new cells per model (+1 on
deepseek), judge two pre-committed gates, and draw two figures.

## δ already stands — D7, restated (not re-opened)

The handoff into this session flagged "pick δ" as M2's headline open choice. The ledger
says otherwise: **D7 (2026-07-06, M0 brief sign-off) committed δ = 0.10 before the
project's first paid call** — the maximally clean version of KICKOFF's "δ set in the
M-brief before any paid run." This brief restates the mechanics so the M2 record is
self-contained, and does not re-open the choice:

- An **equivalence margin** is the pre-declared band inside which two rates count as
  "the same." Claim 2's gate is **containment, not excludes-zero**: the Newcombe 95%
  interval on (lossy_padded − lossy) must sit *entirely inside* ±0.10. (Excluding zero
  proves a difference; containment inside ±δ proves the difference — if any — is too
  small to matter. Equivalence needs the second kind.)
- The margin only protects the claim because it was fixed *before data existed* — the
  same reason D14's ceiling was pre-committed at the headline.
- D7 also pre-committed the N schedule: the claim-2 cell runs at N=40, and if the
  interval isn't contained at 40 it extends **once** to N≈90 before final judgment
  (D7's "a single stray reclaim escalates" phrasing is this rule as seen against a
  clean 0/40 comparator — the general form is below).

## What M0/M1 settled that M2 stands on

- **The banks are M2's input — do not regenerate.** M1's trajectory banks are committed
  under `evidence/m1/` and live in `runs/m1-bank-*` (D15); `m1.py::load_bank` returns
  the taken trials in schedule order. Take rates: llama 0.68 (40 taken), deepseek 0.92
  (90 taken — the escalation top-up included), qwen72b 0.91 (40 taken). D5's pairing is
  the design's spine: every M2 cell is a write-time transformation of the *same*
  session-1 trajectories M1's cells used, so policy comparisons differ by the note
  alone, never by the problem draw.
- **M1's judged cells are M2's comparators — judged once, never re-run (D14).** The
  claim-2 and claim-3 gates below compare *new* cells against M1's archived results
  (lossy@0.1: llama 0/40, deepseek 1/90, qwen72b 0/40; lossy@0.3: 0/40 all three;
  source_first: 40/40 everywhere). Zero M1 cells are re-run in M2.
- **Roster frozen (D13):** llama + deepseek + qwen-2.5-72b-instruct, the 72b labeled in
  every table as a same-family, 10×-size substitution for the paper's qwen-7b. qwen72b
  stays route-pinned to DeepInfra; its throttling can outlast the adapter's 8 retries,
  so its arms run in bounded batches (the grid runner is resume-aware and extends cells
  without duplicates).
- **Sampling and readout are settled, not re-decided.** Temperature 0.0 / max_tokens
  600 (D10) — `m2.py` imports the constants exactly as `m1.py` does. The widened
  `parse_answer` (the escaped-`\$` fix, PR #10) is load-bearing for deepseek and is
  never reverted. The strict parser + the abstain/emit classifier are the same
  everywhere; no new readout is introduced in M2.
- **The checkpoint discipline binds every new cell.** Two M0 scoring bugs and M1's
  escaped-dollar blindspot all passed the validator suite and were caught only by eyes
  on raw replies. Every new M2 cell stops at N=20 for a mandatory hand-read before
  scaling — with M2-specific eyes listed in the design below.

## The design: seven new cells per model (+ blank on deepseek), zero re-runs

Per model, all over the m1 bank in bank order, session 2 = the paper's exact
`[system, note, directed correction]` frame, every note gated per trial:

| cell | serves | N schedule | new note shape to hand-read |
|---|---|---|---|
| lossy_padded@0.1 | claim 2 | 40, ladder → ≈90 | lossy content + PAD filler to sf@0.1's length |
| lossy_padded@0.3 | claim 2 | 40, ladder → ≈90 | premise+conclusion + PAD to sf@0.3's length |
| lossy@0.6 | knob | per D18 | facts + premise + wrong conclusion (source present) |
| lossy@1.0 | knob | per D18 | **the transcript cell** — the full session-1 transcript |
| source_first@0.6 | knob | per D18 | facts + premise + conclusion |
| source_first@1.0 | knob | per D18 | identical string to sf@0.6 (threshold mapping) |
| blank (deepseek only) | claim 3 | 40 | the fixed no-content note (g-independent; logged at g=0.1, the wall locus) |

Facts about these cells worth having in hand before sign-off:

- **The padded note's budget-match is mechanical and gated.** `notes.py` appends the
  fixed PAD sentence ("retained from an archived session log; no additional working was
  preserved") until the padded note is at least the source_first note's length at that
  g — their protocol verbatim. The per-trial gate runs on it in the lossy direction
  (source demonstrably absent), and `test_notes` pins the length property, so a trial
  can't silently run under- or over-informative padding.
- **The transcript cell is the one genuinely new mechanic.** At g=1.0 the lossy policy
  carries the full session-1 transcript instead of a note (their runner's special case,
  ported in M0). `m2.py` needs a small loader for the bank's `trial-XX.jsonl`
  trajectory files; the gate for this cell checks the original question (which carries
  the source) is present in the transcript. Expect it at the reclaim ceiling — it's the
  figure's left anchor: "with everything retained, the correction works."
- **Two quiet protocol facts, both free consistency checks.** (1) sf@0.6 and sf@1.0 are
  the *identical note string* under the threshold mapping — a new replicate pair, given
  the same agreement check M1 ran on its sf pair (disagreement beyond noise means the
  run is broken, stop and look). (2) Above the threshold the lossy and source_first
  templates nearly converge (same facts, premise, and conclusion; one verb phrase
  differs), so the two curves *should* sit together at g ≥ 0.6 — visible convergence up
  top is protocol working as designed, not a bug.
- **The blank cell pairs with everything else.** Its trials run over the same bank, in
  bank order, so the lossy-vs-blank comparison holds the trajectories and problems
  fixed and varies only the memory policy — the counterfactual the title claim is
  about. The blank note never carries the drift value, so a wrong emission there is the
  model *inventing* a figure, not inheriting one; the attractor/other-wrong split is
  reported for both arms.
- **A no-peek pledge, on the record.** Claim 3's lossy comparator is M1's archived
  deepseek lossy@0.1 rows (n=90), whose per-trial outcomes are already logged. As of
  this brief, **nobody has tallied that cell's abstain-vs-emit split** — the M1 gate
  only ever counted reclaims. The counting rule is committed here blind (below), and
  both arms are counted once, at judge time, after the blank cell reaches its final N.

## The gates, mechanically

**Claim 2 (content, not length)** — judged per (model, g) at both wall integrities,
with the settled stats (D4), against M1's archived cells:

1. **Equivalence:** the Newcombe 95% interval on (lossy_padded − lossy) sits entirely
   inside ±0.10 (D7's containment gate).
2. **Separation:** the Newcombe 95% interval on (source_first − lossy_padded) excludes
   zero.

The padded cell's ladder (the general form of D7's rule): judge containment at N=40 —
contained → the component holds; not contained → extend **once** to N≈90 and judge
final. Boundary arithmetic, computed with our `stats.py` against a 0/40 comparator:
0/40 padded gives ±8.8% (contained, clears); 1/40 gives an upper edge of +12.9%
(escalate); 1/90 after escalation gives [−7.7%, +6.0%] (clears). Against deepseek's
1/90 comparator: 0/40 clears at [−6.0%, +7.7%]; 1/40 escalates (+11.8%); 1/90 clears
(±5.0%). **No numeric futility shortcut for padded cells:** the containment boundary
depends on the comparator (4/90 fails against a 0/40 comparator at +10.9% but *clears*
against deepseek's 1/90 at +9.8%), so any fixed cutoff would be wrong on one side;
these cells cost pennies, and the checkpoint's power over them is the hand-read only.

Composition, pre-committed before any data (mirrors D14): a model **clears claim 2**
only if BOTH components hold at BOTH wall g; one-g-only is PARTIAL with the boundary
noted; **v1 clears claim 2 on ≥2 of 3 models**. Escalation feasibility: deepseek's bank
already holds 90 taken; a padded escalation on llama or qwen72b triggers a bank top-up
first (the cost table carries both as contingency lines).

**Claim 3 (worse than empty)** — deepseek only, at the wall:

- **Counting rule (committed blind, 2026-07-07):** a trial is a **wrong emission** iff
  its logged outcome is `emit_attractor` or `emit_other_wrong` — `grader.emitted_wrong`,
  in code with unit tests since M0. Abstain = no parsed ANSWER value or a hedge phrase
  (the author's `probe.py` rule, verbatim — a hedged reply that still carries an ANSWER
  value counts as abstaining, exactly as their pipeline reads it).
- **Gate:** the Newcombe 95% interval on wrong-emission rate (lossy − blank) excludes
  zero. Comparator: M1's archived lossy@0.1 rows (n=90). New cell: blank at N=40.
  Unequal n is fine (D14 precedent); treating the paired arms as unpaired in Newcombe
  errs conservative (D5).
- **Reported with the verdict:** the attractor vs other-wrong split in both arms,
  abstain rates in both arms, and the honest caveat that comparator and blank rows come
  from different run dates (temperature 0.0, same pinned models and routes; the shared
  trajectories are what keep the comparison tight).
- **The abstainers:** llama (1/12 vs 0/12) and qwen72b (0/12 vs 0/12) keep their
  recorded probe NULLs — KICKOFF pre-commits reporting the predicted null plainly, and
  no gate consumes a bigger version of it (D17's rider offers the extension anyway).

**The knob cells** gate nothing: Wilson intervals on the committed figure, per-point N
annotated, plus the sf@0.6 ≡ sf@1.0 replicate check.

**The checkpoint (every new cell, N=20, $0):** hand-read ≥3 randomly sampled trials per
cell against the raw JSONLs before any cell scales past 20. M2-specific eyes: the
padded notes as sent (filler present, source absent, length ≥ the sf note's — the first
padded notes ever to run paid); the transcript cells' assembled context (the full
session-1 conversation, correction appended); the blank replies' classification (claim
3 lives on abstain-vs-emit — read deepseek's blank replies and confirm the hedge rule
reads them the way a human does). Futility applies only where D14 defined it (none of
M2's new cells carry a reclaim ceiling); nothing can clear at 20. The record goes to
`evidence/m2/m2-checkpoint/RECORD.md`, M1's pattern.

## Decisions — pick or veto (recommendation marked; numbering continues DECISIONS.md)

### D16 · Claim 2's cell plan: both wall g × all three models, judged against M1's archived cells

- **A. Both wall g, all three models, comparators = M1's judged cells (Recommended).**
  Six padded cells (3 models × g ∈ {0.1, 0.3}) at N=40 with the containment ladder;
  claim-2 components computed against M1's archived lossy and source_first cells;
  composition as above (both components, both g, ≥2 of 3 models). *Merit:* symmetric
  with claim 1's composition — no reader can ask why the control was held to a weaker
  standard than the headline; zero duplicated cells; ~$0.05 base. *Trade-off:* an
  escalation on llama or qwen72b forces a bank top-up first (llama ≈ $0.015; qwen72b
  ≈ $0.16 and throttle-exposed) — the one genuinely annoying contingency.
- **B. g = 0.1 only.** *Merit:* halves the padded spend and wall-clock. *Trade-off:*
  KICKOFF words claim 2 "at the wall" and claim 1 just set the both-g standard; a
  one-g equivalence leaves "did padding rescue at 0.3?" unanswered to save ~3 cents.
- **C. Fresh lossy comparator arms alongside the padded cells.** *Merit:* same-run
  timing symmetry between the two arms. *Trade-off:* re-runs a judged condition on the
  SAME bank trajectories — only provider nondeterminism can differ — and puts two
  numbers for one cell into the record; judged-once (D14) exists precisely to prevent
  that ambiguity.

*Why A:* it's the full pre-registered claim at the cheapest honest price, and the
composition is fixed before any data exists — the same property that made D14's gate
worth having. The top-up contingency is real but bounded, and it only fires if the data
actually shows a stray padded reclaim.

### D17 · Claim 3's design: a new blank arm against the archived lossy comparator, counted blind

- **A. Blank N=40 on deepseek; comparator = M1's archived lossy@0.1 outcomes; count
  both arms once, at judge time (Recommended).** The counting rule is committed in this
  brief *before* anyone tallies the archived split (the no-peek pledge above); the
  blank cell runs over the same bank trials in bank order. *Merit:* zero re-runs, ~$0.01,
  maximal pairing (same trajectories, same problems, same correction — only the note
  differs); the pre-registration is airtight because the rule was fixed while the
  comparator's split was genuinely unknown. *Trade-off:* the two arms were sampled on
  different dates — reported plainly with the result.
- **B. Fresh lossy emission arm + blank arm, both N=40, same run.** *Merit:* same-day
  sampling symmetry. *Trade-off:* the fresh arm would reuse the same trajectories
  anyway, so only provider noise differs; it duplicates a judged cell (two lossy@0.1
  numbers in the record) and adds ~$0.011 for strictly less clarity.
- **C. Blank at N=20.** *Merit:* cheapest. *Trade-off:* D9's verdict pre-registered
  "measurable at M2's N≈40"; a 0/20 blank arm's Wilson upper bound is 16.1% vs 8.8% at
  40, and the arm costs about a penny — under-powering the title claim to save it is a
  false economy.

**Rider (a) — extend the abstainers' nulls to N=40? (recommended: no).** llama and
qwen72b's claim-3 NULLs are settled probe verdicts under D9's pre-committed tiers; no
gate consumes a larger version, and KICKOFF only asks that the nulls be reported
plainly. Extending (blank cells on both, ~$0.015, emission comparators already archived)
would buy descriptive precision for the M3 comparison table and nothing else. Say yes
only if you want that table tighter.

*Why A:* it's the strongest inference the design allows — the pairing does the work,
the blind commitment does the hygiene — at the lowest cost, with the one weakness
(cross-date sampling) named in the record rather than papered over.

### D18 · The knob fills: N=40 uniform, all three models

- **A. N=40 per knob cell, all three models, standard 20-checkpoint (Recommended).**
  *Merit:* every point on the capstone figure carries the same evidential weight; the
  size is fixed now, so there is no mid-run "this cell looks interesting, extend it"
  call to make later (the flexible-N researcher degree of freedom the project keeps
  closing off); if a knob cell lands mid-range — the wall's onset, the most interesting
  descriptive outcome — N=40 already resolves it. *Trade-off:* roughly doubles the
  knob spend vs B; the transcript cells are M2's biggest line item either way.
- **B. N=20, descriptive-lite.** *Merit:* halves the biggest M2 line item (~$0.10
  saved). *Trade-off:* ceiling cells read [83.9%, 100%] — fine — but a mid-range cell
  reads ±20+ points of mush, and the temptation to extend it after looking is exactly
  what pre-commitment is for.
- **C. Knob on deepseek only.** *Merit:* cheapest. *Trade-off:* two per-model panels on
  the committed figure go half-empty, and the cross-model consistency of the cliff —
  which M1 already bought the banks for — goes unmeasured.

*Why A:* the knob is what makes the capstone figure travel; uniform N is what makes it
honest at a glance. The absolute cost difference is dimes.

## M2 task list, free-before-paid, exit criteria

Order matters: **nothing paid runs until every free check is green**, and the archived
comparator split stays untallied until judge time.

1. **Sign-off** on D16–D18 (this brief).
2. **Build `m2.py` + `test_m2.py`, TDD, $0:** the cell plan above; `load_bank`,
   `ROSTER`, and the N constants imported from `m1.py` (never redefined), sampling from
   `m0.py` (D10); a trajectory loader for the transcript cells; the blank cell wiring;
   the claim-2 containment ladder + both compositions as **pure functions with the
   boundary arithmetic pinned by tests** (the D14 pattern: verdicts pre-committed in
   code so they can't bend after data arrives); the claim-3 counter over logged rows;
   figure subcommands. Full pytest + the anti-rig suite green before any paid call.
3. **New cells to N=20** (padded, knob, blank — models in parallel, qwen72b in bounded
   batches) → **the checkpoint:** hand-read per the M2-specific eyes above; record to
   `evidence/m2/m2-checkpoint/RECORD.md`.
4. **Extend to N=40**; run the padded ladder exactly as it falls (escalations and bank
   top-ups only as the data dictates).
5. **Judge claims 2 and 3** ($0, pure functions of the logged rows + M1's archived
   comparators); verdict tables with every interval into `ROADMAP.md`.
6. **Figures committed:** `docs/figs/m2-knob.png` (the full knob: both policy curves
   across g ∈ {0.1, 0.3, 0.6, 1.0}, padded points at the wall, blank's reclaim point on
   the deepseek panel; `m1-wall.png` stays untouched as M1's committed record) and
   `docs/figs/m2-emission.png` (deepseek wrong-emission rate, lossy vs blank, Wilson
   bars, N annotated — claim 3's picture).
7. **Evidence + ledger + spine close-out, same PR:** `runs/` JSONLs copied to
   `evidence/m2/` (D15); measured cost ledger appended to `ROADMAP.md`; D16–D18
   outcomes into `DECISIONS.md`; `LEARNING.md` M2 teaching note + new words + 3 recall
   questions; README status updated.

**Exit criteria:** a claim-2 verdict per model per wall g with both components'
intervals recorded, judged only by the pre-committed ladder and composition; a claim-3
verdict on deepseek with both arms' splits and the abstainer nulls restated plainly;
the checkpoint hand-read documented; both figures committed; evidence committed per
D15; measured M2 cost in the ledger; all spine updates in the closing PR.

## Cost and wall-clock (from ROADMAP's measured M1 numbers)

Measured session-2 unit costs from M1's grids: llama ≈ $0.00003/call, deepseek
≈ $0.00028/call, qwen72b ≈ $0.00033/call. Transcript cells (full session-1 conversation
in the prompt) are budgeted at ~5× a note call. Estimates carry the usual 1.5–2×
headroom.

| item | calls (approx) | estimate |
|---|---|---|
| padded cells: 2 g × 40 × 3 models | 240 | ~$0.05 |
| knob note cells: lossy@0.6 + sf@0.6 + sf@1.0, 40 × 3 models | 360 | ~$0.08 |
| transcript cells: lossy@1.0, 40 × 3 models (~5× headroom) | 120 | ~$0.10–0.15 |
| blank cell: deepseek, 40 | 40 | ~$0.01 |
| **base M2 (D16-A + D17-A + D18-A)** | ~760 | **≈ $0.25–0.35** |
| contingency: one padded escalation (+50 session-2 calls) | +50 | +$0.01–0.02 each |
| contingency: llama bank top-up to 90 taken (if its padded cell escalates) | ~740 | +$0.015 |
| contingency: qwen72b bank top-up to 90 taken (ditto; throttle-exposed) | ~550 | +$0.16 |
| rider (a) if yes: blank cells on llama + qwen72b | 80 | +$0.015 |
| D18-B instead: knob cells at N=20 | −240 | −$0.10 |

Hard ceiling with every contingency firing: ≈ $0.75. Running project total after M2:
≈ $0.9–1.4 of KICKOFF's "likely under $10", with M3's cross-check cell still to come —
ROADMAP's $2–4 full-v1 extrapolation stands. The binding constraint remains statistics,
not cost.

Wall-clock: ~240–280 session-2 calls per model ≈ 25–45 min each, run in parallel in the
background (M1's pattern); qwen72b in bounded batches with resume (the DeepInfra
throttle can outlast retries); the checkpoint hand-read is human time (~20–30 min). One
evening, plus this sign-off.

## Explicitly NOT in M2

- `bootstrap.py`, the paper-comparison table, the cross-check cell — M3.
- The logic family and the boundary arm — gated post-v1 (D2).
- Re-running ANY judged M1 cell (D14's judged-once), regenerating any bank, any roster
  change, any re-litigation of D7's δ or of M0/M1 verdicts.
- Undirected/generic corrections in paid cells (validator-only, D2); any new task
  family; any new readout beyond the M0-era parser + classifier.

## New words introduced here

- **Equivalence margin (δ)** — the pre-declared band inside which two rates count as
  "the same"; fixed before data so it can't be tuned to fit (D7: ±0.10).
- **Containment gate** — a gate the interval must sit entirely *inside* (proves
  sameness), vs the excludes-zero gate an interval must sit entirely *outside of zero*
  for (proves difference). Claim 2 needs one of each, in that order.
- **Budget-match control** — a condition that equalizes a resource (here: note length
  in characters) so the effect can only be attributed to what remains different (the
  content). lossy_padded is the paper's budget-match for source_first.
- **Comparator cell** — an already-judged cell a new cell is measured against; reused
  as archived, never re-run, so each condition has exactly one number in the record.
- **Descriptive vs gated cells** — gated cells carry a pre-committed verdict rule;
  descriptive cells are measured and plotted (with intervals) but decide nothing. The
  knob fills are descriptive; the padded and blank cells are gated.
- **Transcript cell** — the g=1.0 lossy cell, which carries the full session-1
  conversation instead of a note (the author's special case, ported verbatim) — the
  figure's "nothing was compressed" anchor.
- **Wrong-emission rate** — the fraction of trials where the model confidently commits
  a wrong value on its ANSWER line (attractor or otherwise), as opposed to reclaiming
  or abstaining; claim 3's currency.
- **No-peek pre-commitment** — fixing a counting rule while the data it will count is
  still untallied, even though it already exists on disk — pre-registration hygiene
  for archived data.
