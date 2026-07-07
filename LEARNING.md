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
