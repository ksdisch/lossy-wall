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
