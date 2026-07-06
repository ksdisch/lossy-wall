# M0 Start-of-Stage Brief — the fit-pilot

*Written 2026-07-06 · status: **awaiting Kyle's sign-off on D5–D9** · scope source of truth: `docs/KICKOFF.md`*

## What M0 is, in plain terms

Before the full experiment spends real tokens, M0 answers the two questions that could kill
the project — cheaply:

1. **Does drift take?** Every downstream measurement *conditions on* (only counts trials
   where) the model first commits to the planted wrong value in session 1. If a model won't
   commit, there's nothing to correct, and that model can't carry the experiment.
2. **Is the title claim even measurable at hobby sample sizes?** Claim 3 ("a lossy memory is
   worse than an empty one") needs at least one model that *answers* rather than abstains. A
   small probe tells us whether that gap is big enough to measure at N≈40 trials per cell,
   before we buy the full grid.

M0 also builds the machinery both pilots need — which is most of the harness — and proves the
scoring can't fool itself (the anti-rig suite) **before any paid call**.

Deliverables: ported plumbing, the problems generator + note builder + grader, the anti-rig
validator suite 3/3 green on a deterministic fake, the author's harness installed as a $0
reference oracle, both pilots run, a keep/amber/kill verdict per model, and a measured cost
ledger.

## What the paper settles (fetched 2026-07-06: arxiv.org/html/2606.25449v2 + the reclaim-eval README)

These were open questions in `KICKOFF.md`; the paper HTML and the author's README answer
them, and our design follows:

1. **The session-2 frame is `[system prompt, carried note, directed correction]`.** Session 1
   induces the error: problem statement, a planted wrong intermediate ("a note says the pens
   come to $27"), the model commits to a wrong total, then neutral follow-up turns deepen the
   commitment (the paper checkpoints depths 1/2/4/8). Session 2 is a fresh conversation whose
   *only* inheritance is the note.
2. **`lossy_padded` budget-matching is character padding.** It is exactly the lossy note plus
   topic-neutral filler, extended to at least `source_first`'s character length. That's the
   whole mechanism — settles the "matched budget" mechanics.
3. **The g mapping.** g is the *integrity knob* — what fraction of the memory survives
   compression. At g ≥ 0.5 every policy keeps the source line items; the wall opens below
   0.5: lossy drops the line items and keeps the premise + wrong conclusion (at g = 0.1,
   conclusion only), while source_first keeps the line items and drops the conclusion.
   Source absence is a property of the note *string*, checkable by a token test for the
   line items — exactly our per-trial verification plan.
4. **Scoring reads an ANSWER line, strictly.** Grading takes the committed value on the
   model's ANSWER line; hedging in surrounding prose doesn't count. The *attractor* (the
   inherited stale value) is detected by exact match; abstain-vs-emit is whether any answer
   value is offered at all.
5. **The anti-rig suite is three deterministic checks** run against a *deterministic fake* —
   a tiny stand-in "model" (no network, no cost) built to reclaim **only when the source's
   line-item tokens are present in its context**, so a pass can't be faked by pattern
   matching: (1) the planted premise actually drifts the model; (2) the correction window
   favors the directed arm; (3) the central anti-rig check — when source tokens are absent
   from the note, reclaim fails for *both* arms. The author's harness passes 3/3; ours must
   too. Their DryRun (`python -m reclaim.probe`) and `scripts/reproduce_tables.py` run free,
   no API key.
6. **Their trial economy reuses 8 problems × 3 seeds across cells** (Table 5 reports
   n=96/cell — apparently the 8×3 pool pooled across the four commitment depths; M0 pins
   this down). Context for D5 below. And **per-model drift-take rates are not reported** —
   our drift-take pilot is genuinely additive, and D8's triggers can't be cribbed from the
   paper.
7. **Their install is `pip install -e .` from a repo clone** (no PyPI name); Apache-2.0. It
   goes in a sibling clone *outside this repo* (`~/Projects/reclaim-eval/`) with its own
   isolated venv — D1's wall stays physical: reference + oracle only, never imported here,
   never in `pyproject.toml`.

**Still to pin down in M0 from the reference code** (protocol-fidelity items, not open
choices): the directed correction's verbatim wording, the exact system prompt, which
commitment depth the headline tables use (v1 fixes ONE depth and matches theirs), and the
exact note templates (paper App. A / their `problems.py`).

## What gets ported from decay-pin (lives at `~/Projects/decay-pin`)

Copy-and-adapt, the lineage's settled port method (decay-pin's D1: full control, tiny files,
divergence expected). The rest of decay-pin's harness — agent loop, compaction hook,
tool-call grader — does **not** fit this experiment's shape (two plain chat sessions, no
tools) and is not ported.

| decay-pin | → lossy-wall | What changes |
|---|---|---|
| `client.py` | `client.py` | Same thin OpenRouter wrapper: loud missing-key error, retry policy, model slug required per call. Slugs become the paper trio (`meta-llama/llama-3.1-8b-instruct`, `deepseek/deepseek-chat`, `qwen/qwen-2.5-7b-instruct` — ping verifies the exact names). The per-model reasoning config is re-established empirically: decay-pin found some models silently burn the answer budget on hidden "thinking" unless told not to; ping checks our trio fresh. |
| `stats.py` + `test_stats.py` | `stats.py` + `test_stats.py` | Near-verbatim (D4): Wilson interval, Newcombe difference, `excludes_zero`. Docstring examples re-pointed from violation rates to reclaim rates. (`bootstrap.py`, the robustness appendix, belongs to M3 — not built now.) |
| `ping.py` | `ping.py` | One-call slug verification + reasoning-behavior probe + measured per-call cost, before any arm spends tokens. |

New, purpose-built (all small): `problems.py` (ledger generator), `notes.py` (the four note
policies as *pure functions* — same inputs always give the same note, no hidden state, no
network — so they're testable for free), `grader.py` (ANSWER-line parser + the
abstain / emit-attractor / emit-other-wrong / emit-correct classifier), `runner.py`
(session-1 drift induction, session-2 frame, the per-trial source-absence token gate, JSONL
trajectory logs), `m0.py` (the two pilots), and pytest suites including the anti-rig fake.

## Decisions — pick or veto (recommendation marked; numbering continues DECISIONS.md)

### D5 · Trial independence: fresh problems per trial vs the paper's reuse

- **A. Fresh generated instance per trial (Recommended).** Every trial in a cell gets its own
  freshly generated ledger problem (new items, new numbers). The four policy notes for a
  given trial still derive from the *same* session-1 trajectory — that pairing is native to
  the design (policies are write-time transformations of one trace) and it makes
  cross-policy comparisons fairer, not less fair; treating the arms as unpaired in Newcombe
  then errs on the conservative side. *Merit:* Wilson assumes independent trials — this is
  the design that honestly delivers that. *Trade-off:* diverges from the paper's exact
  trial economy; the cross-check cell (D1) is where paper-faithfulness lives anyway.
- **B. Paper-exact reuse: 8 problems × 3 seeds.** *Merit:* matches their n bookkeeping.
  *Trade-off:* 20+ trials in a cell would repeat the same 8 problem templates, so trials
  cluster and the Wilson interval quietly overstates what N we really have — the exact kind
  of silent statistics bug D4 exists to prevent.

*Why A:* the statistics are the binding constraint; independence is what makes N mean N.

### D6 · Note templates: verbatim vs paraphrase

- **A. Verbatim (Recommended).** Re-type the note templates exactly from paper App. A and
  their `problems.py` into our `notes.py`, with a comment citing the source. Reading their
  code as a protocol reference is sanctioned (D1); *importing* it is not — re-typing with
  attribution keeps the wall.
- **B. Paraphrase.** *Merit:* would show the effect isn't an artifact of one phrasing — a
  robustness point. *Trade-off:* if our numbers then diverge, we can't tell protocol drift
  from real disagreement — it burns riskiest-assumption #4 *and* muddies the cross-check
  cell. Robustness-to-phrasing is a post-v1 luxury.

*Why A:* replication first; the cross-check cell only means something if the protocol matches.

### D7 · Claim 2's equivalence margin δ — value and timing

An *equivalence margin* is the "close enough to call equal" band, fixed **before** seeing
data: claim 2 says lossy_padded ≈ lossy at the wall, and that claim is only honest if
"≈" was defined in advance (δ) rather than drawn around wherever the data landed.

- **A. δ = 0.10, committed now (Recommended).** The Newcombe interval on
  (lossy_padded − lossy) must sit entirely inside ±10 percentage points. Decidable at
  N=40/cell when both cells come in clean at 0 reclaims; **pre-committed escalation rule:**
  a single stray reclaim in either cell widens the interval past 0.10, so the cell extends
  to N≈90 before judging. *Merit:* the tight margin makes claim 2 mean something, and these
  cells cost pennies. *Trade-off:* a noisy cell costs more trials.
- **B. δ = 0.15 at N=40 flat.** *Merit:* robust to a stray reclaim without escalation.
  *Trade-off:* a 15-point "equal" band is loose enough to invite a fair "that's generous"
  from a careful reader.
- **C. Defer to the M2 brief.** *Merit:* decide nearer the data. *Trade-off:* by then M0/M1
  data exists; committing now — before ANY paid call of the project — is the maximally
  clean version of "pre-committed" and costs nothing today.

*Why A:* pennies buy the more defensible margin, and committing before the first API call
removes the researcher degree of freedom completely (decay-pin D11 style).

### D8 · Drift-take kill/swap trigger (per model, pilot N=20)

The paper doesn't report take rates, so these tiers come from cost-and-signal logic: a take
rate t means only fraction t of session-1 trajectories are usable, multiplying session-1
cost by 1/t — and a low t says the paper's precondition barely reproduces on that model.

- **A. Tiered (Recommended).** At N=20 session-1 trajectories: **≥ 14/20 take (70%) →
  green.** **10–13/20 (50–70%) → amber:** audit our session-1 recipe against their
  `experiment.py` once (maybe our induction is off), then proceed with generation inflated
  by 1/t̂ and the weak take noted in the README. **< 10/20 (50%) → trigger fires.** Fired
  path, in order: fidelity audit → swap a same-family sibling (e.g. llama-3.1-70b-instruct,
  qwen-2.5-14b-instruct — the swap pick is its own mini-decision at trigger time) → if two
  models die, v1 proceeds two-model and says so (success criteria need ≥2 of 3). Killing
  llama specifically would also weaken the cross-check anchor (it's the paper's primary
  model) — worth knowing before pulling that trigger.
- **B. Single line at 50%.** *Merit:* simplest. *Trade-off:* treats 55% (usable but
  cost-doubling, worth flagging) the same as 95% (clean).
- **C. Hard line at 70%.** *Merit:* strict. *Trade-off:* kills models the experiment could
  honestly carry at moderate extra cost — too eager for a replication whose roster is
  already only three.

*Why A:* the amber tier is what makes the trigger honest — it distinguishes "broken" from
"expensive but fine," and pre-commits what we do in each case.

### D9 · Disposition-probe powerability threshold (per model, N=12 per arm)

The probe: from taken session-1 trajectories, run session 2 at the wall (g=0.1) with the
lossy note vs a blank memory, 12 trials each, and count *wrong emissions* (an ANSWER line
carrying any incorrect value — attractor or otherwise). Claim 3 lives on the gap
(lossy − blank).

- **A. Tiered (Recommended).** **Gap ≥ 4/12 (≈33 points) → green:** a true gap that size is
  measurable at M2's N≈40. **Gap 2–3/12 → amber:** extend the probe to 24/arm on that model
  before deciding. **Gap ≤ 1/12 → claim-3 null on that model,** reported plainly (the paper
  itself predicts abstainers show no gap). **If no model goes green, claim 3 is
  pre-registered as an honest null** and v1 proceeds on claims 1–2 — that outcome is a
  reportable verdict, not a failure.
- **B. Green at any positive gap (≥ 2/12).** *Merit:* generous, keeps claim 3 alive.
  *Trade-off:* a 2/12 pilot gap routinely melts to nothing at N=40 — we'd be buying a full
  arm on noise.
- **C. Green only at ≥ 6/12.** *Merit:* near-certain power. *Trade-off:* demands the effect
  be enormous in a 12-trial glimpse; risks benching deepseek (disposition +0.83, the model
  expected to carry this claim) on pilot noise.

*Why A:* 4/12 is roughly where the pilot's signal outweighs its noise for an N≈40 follow-up
— generous enough to survive a small pilot, strict enough not to fund an arm on static.

## M0 task list, exit criteria, and the free-before-paid rule

Order matters: **nothing paid runs until every free check is green.**

1. **Port** `client.py` / `stats.py` / `test_stats.py` / `ping.py`; slugs → paper trio.
2. **Build** `problems.py`, `notes.py` (D5/D6 applied), `grader.py`; pytest unit tests green
   — parser tests especially (the paper's own v2 fixed a parser bug; this is where silent
   scoring corruption lives).
3. **Anti-rig suite green, 3/3, $0:** our deterministic fake + the three checks mirrored
   from their probe; runs in pytest; **hard gate before any API call.**
4. **Oracle setup, $0:** clone reclaim-eval to `~/Projects/reclaim-eval/`, isolated venv,
   run their DryRun probe + `reproduce_tables.py`; while there, pin down the fidelity items
   (correction wording, system prompt, headline depth, templates) — reference only.
5. **Ping, ~pennies:** verify the three slugs, establish reasoning behavior, record measured
   per-call cost.
6. **Drift-take pilot:** N=20 session-1 trajectories × 3 models at the fixed depth; take
   classified mechanically (does the ANSWER line commit the planted wrong conclusion?).
   Apply D8 per model; record verdicts.
7. **Disposition probe:** session-2 lossy-vs-blank at g=0.1, N=12/arm × surviving models,
   reusing taken trajectories from task 6. Apply D9 per model; record verdicts.
8. **Cost ledger:** measured M0 spend + an extrapolated full-v1 estimate against the
   KICKOFF's "likely under $10."

**Exit criteria:** anti-rig 3/3 + all pytest green *before* the first paid call; a D8
verdict and a D9 verdict recorded per model; measured cost ledger written; end-of-stage
spine updates (ROADMAP status, D5–D9 outcomes into DECISIONS.md, LEARNING.md note + recall
questions) committed in the same PR as the closing code, per the definition of done.

**Cost estimate:** session 1 is a multi-turn conversation (~depth+2 calls per trajectory),
so the pilot is ~60 trajectories × a handful of short calls + ~72 probe calls + pings —
well under $1 expected on these models; the measured number is itself a deliverable.

**Explicitly NOT in M0:** any claim gate (M1/M2's job), the knob cells g=1.0/0.6 (M2),
`bootstrap.py` and the comparison table (M3), the logic family and boundary arm (gated
post-v1), anything on the never-list (D2).

## New words introduced here

- **Conditioning** — only counting trials where a precondition held (here: the model drifted
  in session 1); reclaim rate is defined *given* drift, so no take → no denominator.
- **Take / drift-take** — the model actually committing to the planted wrong value; the
  precondition every reclaim measurement stands on.
- **Disposition** — a model's lean, when uncertain, toward answering anyway vs abstaining;
  claim 3 needs an answerer.
- **Attractor** — the stale inherited value the model gravitates back to; detected by exact
  match against the planted conclusion.
- **Deterministic fake** — a tiny scripted stand-in "model" whose behavior is fixed by rule
  (reclaims only when source tokens are visible), so validator passes can't be luck.
- **Oracle** — a trusted external answer-source used only to check our results (the author's
  harness), never wired into how we produce them.
- **Pure function** — same inputs, same output, touches nothing else; what makes the note
  builder testable without a model or a network.
- **Equivalence margin (δ)** — the pre-committed "close enough to call equal" band; without
  it, "no difference" claims are unfalsifiable.
- **Escalation rule** — a pre-committed "if the interval is still too wide at N, extend to
  N′" step, so sample size can grow without the growth being data-fishing.
