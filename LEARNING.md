# LEARNING.md — teaching notes and vocabulary, stage by stage

Plain-English notes on what each stage built and *why it's shaped that way*, plus every
new term defined the first time it earns its keep. The goal: being able to defend each
piece to a stranger without notes. (The M0 start-of-stage brief already defined the
stage's core words — conditioning, take, disposition, attractor, oracle, equivalence
margin — in `docs/M0-BRIEF.md`; this file picks up from there.)

---

## M0 — the fit-pilot (2026-07-06)

### The teaching note

**What M0 was for, and what it answered.** Two assumptions could have killed the
project, so M0 bought the answers before the full experiment spends anything: (1) *does
drift take?* — do models actually swallow a planted wrong subtotal and commit to the
wrong total, since every downstream measurement only counts trials where they did; and
(2) *is the title claim measurable at hobby N?* — is there a model that, holding a lossy
note, confidently answers wrong where a blank memory would abstain? Both came back yes.
Drift takes on llama at 14/20 and deepseek at 13/20 (llama green, deepseek amber under
the pre-committed D8 tiers). And the disposition probe found the paper's headline shape
at full strength on deepseek: with a lossy note at the wall it emitted a wrong value in
10 of 12 trials while with a blank memory it abstained 12 of 12 — a +83-point gap whose
Newcombe interval [+46%, +95%] is nowhere near zero. llama showed the same-direction
tiny gap (+1/12, interval straddling zero) — which is exactly what the paper predicts
for an abstainer-disposed model, recorded plainly as a claim-3 null on llama. Claim 3
will live or die on deepseek at M2's N≈40, and on this pilot it looks very alive.

**The day's central lesson: judge-free is not worry-free.** Our scoring never asks an
LLM's opinion — but a mechanical readout can still lie if it reads the wrong *place*.
The first paid trials caught two versions of that, live. First, the **unit trap**: the
take test originally graded the last session-1 reply, but the final follow-up asks for
the total *in cents*, so a model that visibly carried the planted $118 got scored
"didn't take" because it answered 11800. Second, **format drift**: llama commits the
wrong total in plain prose on exactly the restatement turns ("The original pre-tax
total is $118") — no `ANSWER:` line — so a strict parse of any existing turn
under-counts takes on weaker instruction-followers. The fix (D11) is one dedicated
**take-probe turn** appended after the eight follow-ups: "state the pre-tax total you
have been using, as 'ANSWER: <answer>'" — the format demanded inline, which is the
author's own idiom (their correction turn does the same thing, and that's why *their*
parsing works on llama). The probe turn is measurement-only: it is never carried into
session 2, so the carried state stays exactly the paper's depth-8 state.

**Why the anti-rig suite couldn't have caught either bug.** The deterministic fake
answers `ANSWER: <drift>` in dollars, perfectly formatted, on every turn. It validates
the *mechanics* (frames, gates, parsers, the source-token property) but it behaves like
no real model: it never changes units and never drops the format. The general lesson
for this lineage: validators prove the machinery can't fool itself; only hand-reading
real trajectories proves the readout is pointed at the right place. Both failure modes
are now locked in as regression fakes (a cents-aware fake and a format-dropping fake).

**Temperature 0 is not determinism.** D10 runs everything at temperature 0.0 to match
the author's harness — yet the same problems produced different trajectories across
runs (provider-side nondeterminism in serving stacks). That's not a bug for us; it's
the reason the guardrail says get signal from N: statistics carry the result, never a
single greedy sample. The temperature is recorded on every logged row.

**Cheap routes are infrastructure, not abstractions.** Three OpenRouter realities
surfaced in one afternoon: a transient HTTP-200 response whose body is an error with
`choices=None` (the SDK won't retry those — the adapter now retries once, then fails
loudly); a model slug (qwen-2.5-14b-instruct) that simply no longer exists, caught by
ping's free slug check; and a route (qwen-2.5-72b) with two providers where the
fallback provider hard-rejects chat completions — so when the primary rate-limits, the
run dies unless the route is pinned. Every one of these is invisible until real calls
run, which is why ping and the free-before-paid gate exist.

**The pre-committed verdict system worked exactly as designed.** qwen-2.5-7b fired its
D8 trigger (5/20 takes — it re-derives the correct total instead of trusting the
plant; llama and deepseek drift fine on the *same* problems, so it's the model's
disposition, not our recipe). The fired path ran as written: fidelity audit (recipe
verbatim-confirmed), then a same-family swap as a mini-decision — where the live model
list forced a substitution (14b gone → 72b, Kyle's pick) — and then the substitute's
only working provider was throttled hard enough that a 210-call arm couldn't run at
all, so the 72b verdict is deferred to the M1 brief (its 4 completed trials took 3/4)
and M0 closed two-model, a path D8 wrote down in advance. The point worth keeping:
the tiers were decided before any data existed, so none of these outcomes involved
judgment calls after seeing results.

### New words

- **Take-probe / measurement turn** — an extra turn asked only to *read* the model's
  state (here: the committed total, format demanded inline), never carried into any
  later context. Measurement, not protocol.
- **Unit-transform bug** — a readout comparing values in the wrong units (cents vs
  dollars); the reason the take test gets its own turn instead of reading the last
  reply.
- **Format drift** — a model dropping a demanded reply format mid-conversation (llama
  answering restatement turns in prose); why "strict parser" must come with "a turn
  that re-demands the format".
- **Provider nondeterminism** — same prompt, temperature 0, different replies across
  runs, because the serving stack itself varies; why temp 0 ≠ reproducibility and N
  carries the statistics.
- **Provider routing / route pinning** — one OpenRouter slug can be served by several
  backends; a broken fallback backend means a flaky arm until the route is pinned
  (`provider.order` + `allow_fallbacks: false` in the request body).
- **Emission gap** — claim 3's number: wrong-emission rate with the lossy note minus
  wrong-emission rate with a blank note, at the same g.
- **1/t̂ inflation** — if only fraction t̂ of session-1 trajectories take, generating
  N usable trials costs N/t̂ session-1 runs; D8's amber tier prices this in instead of
  killing the model.

---

## M1 — the wall (2026-07-06)

### The teaching note

**What M1 measured, and what it found.** M1 is the headline: once compression drops a
note's *source* (the line items you'd need to recompute) and keeps only its
*conclusion* (the wrong total the model committed to), does a directed correction stop
working? Yes — at full strength, on all three models. Holding a lossy note at the
wall, told exactly where the error is, the roster reclaimed the correct total in 1 of
290 lossy trials (llama 0/80, deepseek 1/130, qwen72b 0/80 across both wall
integrities). Spend the *same character budget* keeping the source instead — drop the
recomputable conclusion, keep the line items — and the correction works every single
time: 240/240 source_first reclaims, with the model visibly redoing the arithmetic in
each sampled reply. Claim 1's pre-committed gate (Wilson-95 upper bound ≤ 0.10 on
every lossy cell; Newcombe gap above zero; both g; ≥2 models) cleared 3-for-3. This is
the paper's RR 0.00 vs 0.99–1.00 wall, reproduced.

**Why "consistent with ~0" needed a ladder, and how the ladder earned its keep.** A
0-for-20 cell does *not* mean the true rate is 0% — the honest Wilson bound says "up
to 16.1%", which is why nothing was allowed to clear at the N=20 checkpoint. The
ladder (D14) pre-committed what every outcome would mean before data existed: 0/40
clears (bound 8.8%), 1–3 strays buy one extension to N≈90, ≥4 is final failure. And
then reality used it: deepseek's lossy@0.1 cell produced exactly one "reclaim" — a
hand-read showed the model *assuming* a plausible round subtotal with no source in
context and landing on the true total by pure luck ($150, attractor $157). Strict
scoring keeps it (the commitment is the value; unscoring it by judging the process
would bend the gate) — so the cell escalated, ran 50 more trials, gained nothing, and
cleared at [0.2%, 6.0%]. A stray neither killed the claim nor got waved through; it
bought a bigger sample. That's what pre-commitment is *for*.

**The day's central lesson, round two: the hand-read caught a live parser bug the
fakes never could.** The very first advisory look at raw bank replies showed deepseek
writing `ANSWER: \$197` — the dollar sign LaTeX-escaped — on about a third of its
replies. Our parser (re-typed verbatim from the author's) read that as "no numeric
commit," so true takes were being scored as no-takes. Fixed with regression tests
(PR #10), the blast radius was all in the conservative direction, and re-scoring M0's
archived evidence *revised an M0 verdict upward*: deepseek's pilot was really 20/20
GREEN, not 13/20 AMBER — the ×1.54 cost mandate had been a parser artifact. Two
lineage lessons compound here: (1) M0's "eyes on raw replies" rule found in one sample
what 92 green tests couldn't, because deterministic fakes only validate mechanics;
(2) committing evidence (D15) is what made re-scoring M0 possible at all — you can't
re-derive verdicts from evidence you didn't keep. Bonus protocol note for M3: the
author's parser shares the blindspot, so their deepseek cells may under-read the same
way at the cross-check cell.

**The infrastructure story had a happy ending.** The 72b slot that M0 couldn't run
(provider throttled past 8 retries, twice) completed its bounded D13 re-attempt
cleanly the next session: 18/20 takes, GREEN — and then its bank hit the same 429
throttle mid-build and *lost nothing*, because M1's bank is resume-aware and
append-only (a deliberate divergence from m0.py's replace-on-rerun pilots: the bank
is a durable asset, M2's input, so it extends rather than re-runs). One retry later
it finished at a 0.91 take rate. Total cost of the third model, pilot to verdict:
about $0.20 — and it bought claim 1 its "3 of 3" instead of "2 of 2".

### New words

- **The ladder / judged looks** — the pre-committed N schedule (checkpoint 20 → judge
  40 → one escalation to ≈90) where each look's *powers* are fixed in advance: the
  checkpoint can only stop or continue, never clear; the judge point clears or
  escalates; the escalated look is final.
- **Lucky recovery / lucky confabulation** — a no-source reply that guesses its way
  to the true value (deepseek's 1/130); kept as a reclaim under strict scoring, and
  the reason "consistent with ~0" is a ceiling rather than "exactly 0".
- **Resume-aware / append-only runner** — a driver that extends its logged state
  instead of replacing it (the bank, the grid); what makes an escalation cheap and a
  mid-run throttle harmless.
- **Replicate cells (in practice)** — sf@0.1 and sf@0.3 carry the identical note
  string, so their agreement (+0% on every model) is a free run-integrity check that
  costs two cells' pennies.
- **Escaped-dollar blindspot** — `ANSWER: \$197` parsing as "no commit"; the M1
  instance of the lineage's recurring failure class (unit trap, format drift, now
  LaTeX escaping): a mechanical readout pointed at the right place but reading too
  narrowly.

---

## M2 — the controls (2026-07-07)

### The teaching note

**What M2 measured, and what it found.** M1 showed the wall; a skeptic has two exits
left. Exit one: "the source-first note is longer — maybe the model just needed more
text." M2 closed it with the **budget-match control**: the same lossy note, padded
with an explicitly content-free filler sentence until it's at least as long as the
source-first note. If length were doing the work, padding would rescue reclaim. It
rescued nothing — padded cells reclaimed 2 of 350 trials across three models (both
strays hand-read lucky guesses), statistically indistinguishable from plain lossy
inside the pre-committed ±10% band, while source-first beat the padded note by at
least +87.6% everywhere. Same characters spent; only what they *say* differs. **Claim
2 cleared 3 of 3 models.** Exit two: "fine, the note can't be corrected — but surely
carrying *something* beats carrying nothing." Backwards, says the title claim, and
now the measurement: over the *identical* session-1 trajectories, deepseek holding a
**blank** note ("no figures were retained") declined 40/40 times; holding the lossy
note it confidently emitted a wrong number 52/90 times (33 of them the exact stale
value it had committed in session 1). Gap +58%, Newcombe floor +44.2%. **Claim 3
cleared.** The lossy note isn't degraded memory — it's an error generator that a
blank memory simply doesn't have.

**Equivalence is a different kind of proof.** Claim 1 needed a *difference* (interval
excludes zero). Claim 2's first component needed *sameness* — and you can't prove
sameness by failing to find a difference; you prove it with a **containment gate**:
the interval on (padded − lossy) must sit entirely inside a band (±δ = ±0.10, D7)
that was fixed before any data existed. The band is what makes "they're the same"
falsifiable: land outside it and the claim dies. Both kinds of gate ran side by side
in every claim-2 cell — containment for "padding didn't help," excludes-zero for
"the source still does."

**The ladder earned its keep twice more — and the boundary arithmetic mattered.**
Both wall-g padded conditions produced exactly one stray reclaim each (deepseek at
g=0.1, qwen72b at g=0.3; both models *assuming* a value with no source in context
and hitting the truth by luck — kept as reclaims, because strict scoring judges the
committed value, not the process). Both cells escalated exactly as D16 pre-wrote:
50 more trials each, zero further reclaims, contained at 1/90. qwen72b's escalation
first forced the priced contingency — its bank grew from 40 to 90 taken trajectories
($0.17, three throttle-safe batches) — proof that pre-pricing contingencies is what
lets you execute them without flinching. And the reason D16 banned any fixed
futility cutoff showed up in the real numbers: 1/40 escalates against a 0/40
comparator (+12.9%) but the same count against deepseek's 1/90 comparator is a
different boundary (+11.8%) — the gate is a *relation between two cells*, not a
property of one.

**The no-peek pledge, kept by a machine.** Claim 3's comparator rows had been on
disk since M1 — but their abstain-vs-emit split was deliberately never counted while
the counting rule was being written. This session made the pledge mechanical:
`m2.judge` refuses to tally either arm until the blank cell reaches its final N
(a unit test pins the refusal). When the count finally ran, it was the first time
anyone — human or model — saw the 52/90. That's what pre-registration hygiene looks
like when archived data is involved: fix the rule while the answer is still unknown,
then make peeking impossible rather than merely forbidden.

**One honest wrinkle, read with eyes.** llama's knob cells dipped below the ceiling
(65–95% where the other models sat at 100%). The mandatory checkpoint's targeted
read showed why: llama rambles into verification loops and hits the 600-token cap
without ever writing an ANSWER line (scored abstain — several such replies contain
the correct total, uncommitted), and sometimes re-commits the carried wrong total
*after deriving the correct one* (scored emit_attractor — the brittle-memory failure
mode showing up even with the source in hand). The readout is the author's,
verbatim, applied evenly; the dip is llama being llama, reported as a caveat on the
figure rather than smoothed away. Descriptive cells get honesty, not rescue.

### New words

- **Budget-match control** — a condition that equalizes a resource (here: note
  length in characters) so any remaining effect must come from what differs (the
  content). `lossy_padded` is the paper's budget-match for `source_first`.
- **Equivalence margin (δ)** — the pre-declared band inside which two rates count as
  "the same" (D7: ±0.10). Fixed before data so it can't be tuned to fit.
- **Containment gate** — a gate an interval must sit entirely *inside* (proves
  sameness), vs the excludes-zero gate it must sit entirely *outside zero* for
  (proves difference). Claim 2 needed one of each.
- **Comparator cell** — an already-judged cell a new cell is measured against,
  reused as archived and never re-run (judged once), so each condition has exactly
  one number in the record.
- **Descriptive vs gated cells** — gated cells carry a pre-committed verdict rule;
  descriptive cells are measured and plotted with intervals but decide nothing. The
  knob fills are descriptive; the padded and blank cells are gated.
- **Transcript cell** — the g=1.0 lossy cell, which carries the full session-1
  conversation instead of a note (the author's special case, verbatim) — the
  figure's "nothing was compressed" anchor.
- **Wrong-emission rate** — the fraction of trials where the model confidently
  commits a wrong value on its ANSWER line, as opposed to reclaiming or abstaining;
  claim 3's currency.
- **No-peek pre-commitment** — fixing a counting rule while the data it will count
  is still untallied even though it already exists on disk; here, enforced in code
  (the judge refuses to count early).

### Recall questions

1. Padding the lossy note to the source-first note's exact length changed nothing;
   the source-first note at the same budget reclaimed essentially always. What
   objection does that pair of facts kill, and why does killing it need *both*
   gates (containment AND separation) rather than either alone?
2. deepseek's blank arm abstained 40/40 while its lossy arm wrong-emitted 52/90 on
   the same trajectories. Why does the project describe the lossy note as "worse
   than nothing" rather than "less useful than the source"? What exactly does the
   blank note remove that silences the errors?
3. The claim-3 counting rule was committed on 2026-07-07 while the comparator's
   split sat uncounted on disk from M1 — and `m2.judge` refuses to tally it before
   the blank cell's final N. What could a skeptic allege if the split had been
   peeked at first, and why is the *code-level* refusal stronger than a promise?

## M3 — cross-check + capstone (2026-07-08)

### The teaching note

**What M3 measured, and what it found.** M0–M2 measured everything; M3 asked one last
question about *us*: did our from-the-paper rebuild actually implement the paper's
protocol, or did three CLEARED claims come from a harness that quietly drifted into
measuring something easier? You can't answer that by re-running our own code — any bug
would just reproduce itself. So M3 ran the one experiment we never ran: the **author's
own released harness**, unmodified, in its own venv, on the paper's own cell economy
(32 fixed problems × 3 seeds = n=96/cell, llama, all three policies, all four
integrities — 4,896 calls, $0.055), and compared its cells against our archived ones
with the same Newcombe machinery every other gate used. The pre-committed criterion:
six overlap cells at wall g; **AGREE** iff every interval on (their rate − ours)
contains zero. All six did — lossy 0/96 and 1/96 against our 0/40s, source_first
96/96 against our 40/40s. Two codebases, written by different people from the same
paper, one number apart across 576 gated trials. That's what "the protocol description
is complete enough to reproduce from" looks like when it's true — and it was the
project's riskiest assumption from day one.

**A replication is not a re-run.** Running their code again would have tested *their
code*. Building from the paper and then meeting their code at one cell tests *the
paper* — whether its words are sufficient instructions. That's why D1 made the
cross-check a single oracle cell rather than the whole experiment: the oracle's job is
calibration, not measurement. And "oracle" never meant infallible — the same milestone
mechanically proved their parser mis-reads escaped `ANSWER: \$197` lines as
abstentions (0/8 archived deepseek commits parsed; ours reads 8/8; plain controls
agree 4/4), reconfirmed their table-replay script fails on its own shipped artifact,
and caught the paper and their README disagreeing in the last digit on three wall
cells. Trust the protocol, verify the readouts — in both directions.

**The degeneracy lesson, now shown rather than told.** The paper reports bootstrap
intervals; our gates ran Wilson. D4 promised the side-by-side, and the appendix
delivered it: 39 rows, zero disagreements on any gate — the method choice never drove
a verdict. But look at any 0/40 cell: the bootstrap interval is [0.000, 0.000].
Resampling can only redraw what it saw, and 40 zeros redraw as 40 zeros, five thousand
times — maximal confidence exactly where the evidence is thinnest. Wilson says
[0%, 8.8%]: "consistent with zero, not proved zero." That gap between the two answers
IS the argument for D4, sitting in a committed table instead of a footnote.

**Estimates err; pre-commitment absorbs it.** The run cost half the envelope's floor
($0.055 vs $0.08–0.15) but took ~7.6h against a 2.5–4.5h guess — the provider was
slow, not the plan wrong. Because the run was staged (smoke → checkpoint → resume),
checkpointed per unit, and running in the background, a 3× wall-clock miss cost
nothing but patience. The M3 checkpoint did its only jobs: the recount matched their
console exactly, nine sampled rows told one coherent story against the dumped
truth/drift values, and the per-unit cost confirmed the resume's price before it was
paid.

### New words

- **Oracle run** — the one paid execution of the author's own harness, used as an
  external reference to check our independent build against; "oracle" as in *trusted
  reference point*, not *infallible* — its two known defects are part of the report.
- **Replication vs re-run** — a re-run executes the author's code and tests the code;
  a replication rebuilds from the paper's description and tests the *description*.
  The cross-check cell is where the two meet.
- **Paper economy** — the paper's own trial bookkeeping (32 fixed problems × 3 seeds,
  session 1 rebuilt per policy) as opposed to our D5 economy (fresh problem per
  trial, one trajectory shared across policies). Both valid; the table labels both.
- **Agreement criterion** — the pre-committed rule for "two builds got the same
  result": every gated overlap cell's Newcombe interval on (theirs − ours) contains
  zero. Chosen before the run existed, tolerant of noise (even 8/96 vs 0/40 passes),
  sharp on structure (a 12-point source-first drop fires).
- **Protocol-fidelity line** — the cross-check's verdict, reported *beside* the claim
  verdicts rather than compounded into them (D20): "what we measured" and "whether
  two builds agree" are different facts and stay separately falsifiable.
- **Degenerate interval** — an interval that collapses to a point because resampling
  can't produce variation (0/40 → [0.000, 0.000]); the bootstrap's failure mode at
  extreme cells and the reason Wilson decides gates.
- **Resume-safe checkpointing** — their runner's append-per-unit discipline: a crash
  or throttle loses at most one unit, and a re-invocation pays only for what's
  missing. What made "smoke then resume" a free staging structure.

### Recall questions

1. The cross-check ran the author's harness, not ours, on the overlap cells. Why
   would re-running *our* harness have proven nothing about protocol fidelity — and
   what specific risk from the kickoff does the AGREE verdict retire?
2. Every one of our 0/40 lossy cells wears Wilson [0%, 8.8%] but bootstrap
   [0.0%, 0.0%]. Explain to a skeptic why the narrower interval is the *less*
   trustworthy one there, and which decision (D-number) that argument justifies.
3. The fixture check proved their parser reads `ANSWER: \$197` as an abstention, yet
   the comparison table says this "may under-read escaped commits" only *shrinks*
   their deepseek lossy−blank gap. Walk the direction: why can that bug only make
   their Δ+0.83 a floor rather than an artifact?

---

## M4 — the logic family: a soft wall, a real confound, and a bug the checkpoint caught

M4 asked whether the brittle-memory effect survives a change of task — arithmetic ledgers →
constraint-deduction puzzles. Plain answer: **yes, but softly, and only where the correction is
unambiguous.** deepseek reproduced it cleanly (fix recovers 100%, the lossy floor collapses, and
— the money shot — a note that *keeps the corrupted premise* drives 45–70% inheritance, worse
than dropping it). qwen did not, and the *why* is the lesson: on ordering puzzles the directed
correction "the X-vs-Y order was wrong" is really a *flip* instruction, and qwen flips whatever
it's shown — the bare drift conclusion (→ correct, inflating lossy) or the true fact (→ the drift,
breaking source_first). deepseek recomputes instead of flipping, so it's immune. That interaction
— not any code defect — is why M4 is PARTIAL rather than REPRODUCED.

Two process lessons compounded from earlier milestones. First, **the take-probe bug**: the same
D11 failure that bit arithmetic (llama drops the ANSWER format and commits in prose) recurred on
logic because the logic take-probe was never made format-explicit — and 222 green tests missed it
because the deterministic fake always emits a clean ANSWER line. The mandatory hand-read caught a
*perfect 0/20* that should have been ~50%, saving the paper's anchor model from a false benching.
Second, **the checkpoint is not a formality**: it wasn't a scoring bug this time, but the same
hand-read is what surfaced the ordering confound — before the N=60 spend, not after. A too-clean
number (a perfect 0, a perfect even/odd split, a negative gap) is always worth a hand-read.

### New words

- **Soft wall** — a wall whose lossy floor does not collapse to ~0 (logic: 0.23–0.75), because a
  strong model can partially re-derive the answer in a tiny closed set; the fix still wins *where
  the correction is clean*, but the floor is a property of the task, not the model.
- **Chance floor** — with k closed options a pure guesser scores ~1/k; on logic (k=3–5) this makes
  raw reclaim rate a noisy read, so the recov/inherit/novel/abst taxonomy carries the interpretation.
- **Emission taxonomy (recov / inherit / novel / abst)** — the four ways a logic reply lands.
  `novel`=0 everywhere was the diagnostic tell in M4: qwen's source_first errors were *exactly* the
  planted drift, never a random wrong token — proof the drift was *produced by the correction-flip*,
  not by mis-solving.
- **Directed-correction confound** — a correction that names an error locus can, on ordering
  puzzles, function as a flip instruction; applied to a true source it manufactures the wrong
  answer. A protocol behaving differently on a task family it wasn't designed around — a first-class
  finding, not a bug to hide.
- **Take bias → bank composition** — a model only banks trajectories where the drift *took*;
  deepseek takes ordering drift readily but refuses assignment drift (it contradicts an explicit
  constraint), so its bank is ordering-heavy and the clean assignment stratum is underpowered.

### Recall questions

1. deepseek's lossy reclaim is 0.65 at g=0.1 but 0.23 at g=0.3 — *higher* at the more-degraded
   note. That looks backwards. Explain the mechanism (what differs between the g=0.1 and g=0.3
   lossy notes) and why it is the brittle-memory thesis rather than a contradiction of it.
2. Every one of qwen's source_first errors was `inherit` (the drift) and *zero* were `novel`. Why
   is that specific zero the evidence that ruled out "qwen just mis-solves the puzzle" and pointed
   at the directed correction — and which stratum (ordering/assignment) did it localise the effect to?
3. The take-probe bug made llama read 0/20 when it truly took 9/20, and 222 tests stayed green.
   Name the property of the deterministic fake that made those tests structurally blind to it, and
   the one project rule that turned the bug from silent-in-the-grid into caught-at-the-checkpoint.
