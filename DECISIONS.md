# DECISIONS.md — the running ledger of real choices

One entry per decision that shaped the project: the options that were on the table, what
was picked, and *why* — so every choice can be defended later without archaeology. D1–D4
were argued at the kickoff interview (2026-07-06) and their outcomes recorded in the Gate
record of `docs/KICKOFF.md`; this ledger carries them plus everything decided since.

---

## D1 · Harness: build our own + one pre-committed cross-check cell

- **Date / decider:** 2026-07-06 / Kyle (at the kickoff gate)
- **Options:** (A) build the harness in-repo, with ONE pre-committed cross-check cell run
  through the author's released harness (`reclaim-eval`, Apache-2.0); (B) adopt the
  author's harness as our runner; (C) build in-repo with no cross-check at all.
- **Decision: A — independent build + cross-check cell.**
- **Why:** an independent build is what makes this a *replication* — it tests whether the
  paper's protocol description is complete enough to reproduce from (riskiest assumption
  #4), which re-running the author's own code never could. The cross-check cell keeps us
  honest in the other direction: our harness vs theirs on one overlapping cell, agreement
  or disagreement reportable either way, and disagreement triggers a protocol audit.
  Hard constraint carried into the code: the author's package is a protocol reference +
  cross-check **oracle only** — installed in an isolated venv for that stage, never
  imported by our harness code, never in `pyproject.toml`.

## D2 · v1 scope: arithmetic-only, four-point g-sweep, three policies + blank, directed only

- **Date / decider:** 2026-07-06 / Kyle
- **Options:** where to draw the v1 line — (A) the narrow cut: ONE task family
  (arithmetic ledgers, the hard wall), integrity knob g ∈ {1.0, 0.6, 0.3, 0.1} with wall
  cells first, policies lossy / lossy_padded / source_first at matched character budget
  + blank at the wall, directed corrections only; (B) A plus the paper's logic family
  and/or source-size boundary arm inside v1; (C) wider reproductions the paper offers
  (deployed memory systems, MultiWOZ, cascade, adversarial battery, disposition sweep).
- **Decision: A — the narrow cut**, with the logic family and boundary arm **gated
  post-v1** (only if the effect shows) and the C-list **never**.
- **Why:** v1's job is the thinnest slice that decides the headline claims: the wall on
  the hard family, with exactly the controls that make the three claims decidable
  (lossy_padded isolates content-vs-length; blank carries worse-than-empty). Arithmetic
  is where the paper's wall is starkest — reclaim rate (RR) 0.00 vs 0.99–1.00 — so an
  effect *and* a null are both informative there. Gating keeps the extensions earned
  rather than paid for up front, and the never-list (no deployed systems, no frontier
  replay, no LLM-judge grading, ever) keeps v1 one legible deliverable.

## D3 · Model roster: the paper trio

- **Date / decider:** 2026-07-06 / Kyle
- **Options:** (A) the paper's trio — llama-3.1-8b-instruct, deepseek-chat, qwen-2.5-7b,
  all via OpenRouter; (B) carry over decay-pin's proven roster (GLM-5.1 / Qwen3.6-27B /
  Gemini-3.5-flash); (C) a smaller or larger cheap-model set.
- **Decision: A — the paper trio.**
- **Why:** llama-3.1-8b-instruct is the paper's own primary model, buying direct
  comparability and anchoring the cross-check cell (D1); deepseek-chat brings the
  roster's strongest answering disposition (+0.83, per the paper) and therefore carries
  claim 3 — worse-than-empty needs a model that *answers* rather than abstains;
  qwen-2.5-7b adds a second model family at a middle point. Hobby scale is this paper's
  native scale — its primary model is an 8B — so matching its roster costs nothing.
  Hedge: dispositions can shift under model updates, so M0's drift-take pilot and
  disposition probe carry a pre-committed kill/swap trigger per model.

## D4 · Statistics: Wilson/Newcombe decide the gates; bootstrap as robustness appendix

- **Date / decider:** 2026-07-06 / Kyle
- **Options:** (A) Wilson CIs on each cell + Newcombe CIs on differences decide every
  claim gate, plus a small bootstrap appendix mirroring the paper's method; (B)
  bootstrap-only, matching the paper exactly; (C) Wilson/Newcombe only, no bootstrap.
- **Decision: A — Wilson/Newcombe decide; bootstrap is robustness only.** On any
  disagreement, Wilson decides and the discrepancy is reported.
- **Why:** a reclaim rate is a proportion, and proportions get proportion intervals —
  the settled methodology of the whole lineage (`stats.py` ports near-verbatim from
  decay-pin). The paper itself reports bootstrap CIs, so a small `bootstrap.py` addendum
  makes the comparison table honest: our Wilson intervals beside their bootstrap
  intervals, labeled as different methods. Pre-committing which method decides removes a
  researcher degree of freedom — no picking whichever interval flatters the claim.

## D5 · Trial independence: fresh generated problems, one per trial

- **Date / decider:** 2026-07-06 / Kyle (M0 brief sign-off; full options in
  `docs/M0-BRIEF.md`)
- **Options:** (A) a freshly generated ledger problem for every trial in a cell — the four
  policy notes for a trial still derive from the *same* session-1 trajectory, a pairing
  that's native to the design (policies are write-time transformations of one trace);
  (B) the paper's exact trial economy, 8 problems × 3 seeds reused across cells.
- **Decision: A — fresh per trial.**
- **Why:** Wilson intervals assume independent trials; reusing 8 problem templates makes
  trials cluster, so N quietly means less than N — the silent-statistics bug D4 exists to
  prevent. The cross-policy pairing is kept (it makes comparisons fairer), and treating
  paired arms as unpaired in Newcombe errs conservative. Paper-faithful bookkeeping lives
  where it belongs: the cross-check cell (D1).

## D6 · Note templates: verbatim from the paper

- **Date / decider:** 2026-07-06 / Kyle (M0 brief sign-off)
- **Options:** (A) re-type the note templates exactly from paper App. A and the author's
  `problems.py` into our `notes.py`, with a comment citing the source; (B) paraphrase
  them, as a robustness-to-phrasing point.
- **Decision: A — verbatim.**
- **Why:** replication first. Protocol fidelity is riskiest assumption #4, and the
  cross-check cell only means something if the protocol matches; if paraphrased numbers
  diverged, we couldn't tell protocol drift from real disagreement. Reading their code as
  a protocol reference is sanctioned (D1); importing it never is — re-typing with
  attribution keeps that wall. Robustness-to-phrasing is a post-v1 luxury.

## D7 · Claim 2's equivalence margin: δ = 0.10, committed now

- **Date / decider:** 2026-07-06 / Kyle (M0 brief sign-off)
- **Options:** (A) δ = 0.10, committed before the project's first paid call, with a
  pre-committed escalation rule — claim 2's cell runs at N=40 and a single stray reclaim
  (which alone widens the Newcombe interval past ±0.10) extends it to N≈90 before
  judging; (B) δ = 0.15 at N=40 flat, no escalation needed; (C) defer the choice to the
  M2 brief.
- **Decision: A — δ = 0.10 now, escalation pre-committed.**
- **Why:** an equivalence margin only protects the claim if it's fixed before data
  exists; committing before ANY paid call is the maximally clean version, and it costs
  nothing today. The tight margin makes "lossy_padded ≈ lossy" mean something (0.15 is
  loose enough to invite "that's generous"), and these cells cost pennies, so the
  escalation is cheap insurance. Gate mechanics: the Newcombe interval on
  (lossy_padded − lossy) must sit entirely inside ±0.10 — containment, not
  `excludes_zero`.

## D8 · Drift-take kill/swap trigger: tiered at N=20 per model

- **Date / decider:** 2026-07-06 / Kyle (M0 brief sign-off)
- **Options:** at N=20 pilot session-1 trajectories per model — (A) tiered:
  **≥ 14/20 take → green**; **10–13/20 → amber**: audit our session-1 recipe against the
  author's `experiment.py` once, then proceed with generation inflated by 1/t̂ and the
  weak take noted in the README; **< 10/20 → the trigger fires**: fidelity audit → swap a
  same-family sibling (the swap pick is its own mini-decision at trigger time) → if two
  models die, v1 proceeds two-model and says so. (B) a single line at 50%. (C) a hard
  line at 70%.
- **Decision: A — tiered.**
- **Why:** the amber tier is what makes the trigger honest — it distinguishes "broken"
  from "expensive but fine" and pre-commits the response to each, where B hides
  cost-doubling weakness and C kills models the experiment could honestly carry. The
  paper reports no take rates, so the tiers come from cost-and-signal logic (a take rate
  t multiplies session-1 cost by 1/t and, when low, says the paper's precondition barely
  reproduces). Known before any trigger pull: killing llama specifically would weaken the
  cross-check anchor (it's the paper's primary model).

## D9 · Disposition-probe powerability: tiered at N=12 per arm

- **Date / decider:** 2026-07-06 / Kyle (M0 brief sign-off)
- **Options:** per model, wrong-emission gap (lossy − blank) at g=0.1, 12 trials per
  arm — (A) tiered: **gap ≥ 4/12 → green** (a true gap that size is measurable at M2's
  N≈40); **2–3/12 → amber**: extend the probe to 24/arm before deciding; **≤ 1/12 →
  claim-3 null on that model**, reported plainly; **no green model → claim 3 is
  pre-registered as an honest null** and v1 proceeds on claims 1–2. (B) green at any
  positive gap (≥ 2/12). (C) green only at ≥ 6/12.
- **Decision: A — tiered.**
- **Why:** 4/12 is roughly where a 12-trial pilot's signal outweighs its noise for an
  N≈40 follow-up; B routinely funds a full arm on noise that melts at N=40, and C
  demands the effect be enormous in a 12-trial glimpse — risking benching deepseek (the
  model the paper's disposition score says should carry claim 3) on pilot noise. The
  null path is a reportable verdict, not a failure — `docs/KICKOFF.md` pre-commits it.

## D10 · Sampling: temperature 0.0 / max_tokens 600 — match the author's harness

- **Date / decider:** 2026-07-06 / Kyle (mid-M0, before the first pilot ran)
- **Options:** (A) temperature 0.0 and max_tokens 600, exactly their
  `reclaim-eval/src/reclaim/llm.py`; (B) provider-default temperature (~1.0), closer
  to how the models run in the wild.
- **Decision: A — match the paper.**
- **Why:** protocol fidelity is riskiest assumption #4, and the cross-check cell (D1)
  only reads cleanly if sampling matches — the same logic that picked D6's verbatim
  templates. If our rates diverged from theirs under a different temperature, protocol
  drift and sampling noise would be indistinguishable. The CLAUDE.md guardrail ("don't
  chase determinism via temp 0 — get signal from N") is satisfied, not violated:
  trial-to-trial variation comes from D5's fresh problems, the temperature is recorded
  on every logged row, and no determinism is claimed — the paid trials themselves
  showed run-to-run variation at temp 0.0 (provider-side nondeterminism), which is why
  N carries the statistics.

## D11 · Drift-take readout: a dedicated take-probe turn, never carried

- **Date / decider:** 2026-07-06 / Kyle (mid-M0, after hand-reading the first paid
  trajectories)
- **Options:** (A) one dedicated measurement turn appended after the 8 follow-ups —
  "state the pre-tax total you have been using, as 'ANSWER: <answer>'" — the format
  demanded inline (the author's own correction-turn idiom), graded by the same strict
  parser as everything else, and NEVER carried into session 2 (the depth-8 state stays
  exactly their `states[max(DEPTHS)]`); (B) read the deepest session-1 turn that
  happens to carry a parseable ANSWER line; (C) a looser session-1-only parser (fall
  back to the last dollar figure in the confirm reply).
- **Decision: A — the take-probe turn** (+1 call per trajectory, ~11% more session-1
  spend — pennies).
- **Why:** the first paid trials produced two live findings that kill the naive
  readouts. (1) The last follow-up converts the running total to CENTS, so grading the
  final reply against `problem.drift` mis-scores a visibly taken trajectory. (2) llama
  drops the ANSWER format on precisely the two dollar-restatement turns — it commits
  the planted wrong total in prose there — so ANY strict parse of existing turns
  under-counts take, and B would grade the cents or half-the-total turns instead
  (wrong quantities). C reintroduces the loose-parsing failure class the paper's own
  v2 parser fix removed. A keeps ONE parser, strict everywhere; the take test is our
  addition (D8 — the author's runner never checks drift), so the readout locus is ours
  to define, and a format-explicit measurement turn is the honest mechanical one.
  Bonus lesson recorded in fake.py: the DriftFake answers dollars with a perfect
  ANSWER line on every turn, so the anti-rig suite could never have caught either
  failure — deterministic fakes validate mechanics, not real-model behavior.

## D12 · The qwen slot: trigger → swap → infrastructure block → two-model close

- **Date / decider:** 2026-07-06 / Kyle (the swap picks; the two-model close follows
  D8's pre-committed path)
- **What happened, in order:** qwen-2.5-7b fired its D8 drift-take trigger (5/20
  takes, Wilson [11%, 47%] — the whole interval below the 50% line; hand-read
  trajectories show it re-deriving the correct total rather than trusting the plant,
  while llama/deepseek drift fine on the same problems). Fired path: fidelity audit
  (recipe verbatim-confirmed) → same-family swap. Kyle picked qwen-2.5-14b-instruct;
  OpenRouter no longer lists 14b/32b instruct (ping's free slug check caught it), so
  Kyle subbed qwen-2.5-72b-instruct. The 72b route then proved unrunnable today: its
  fallback provider (Novita) hard-400s chat completions, and its working provider
  (DeepInfra) was throttled upstream past 8 backoff retries, twice — 4 trials
  completed (3 takes, promising) out of 20.
- **Decision: M0 closes two-model (llama + deepseek);** the 72b re-attempt is deferred
  to the M1 start-of-stage brief (route recovery or a direct provider key are both
  plausible by then).
- **Why:** M0's two riskiest-assumption questions were already answered on the
  survivors, D8 pre-commits the two-model path in writing, and holding the milestone
  hostage to a third-party throttle buys nothing the M1 brief can't buy later with
  the same $0.06. KICKOFF's success criteria need ≥2 of 3 models — satisfied.

## D13 · The 72b slot: one bounded re-attempt, then the roster freezes

- **Date / decider:** 2026-07-06 / Kyle (M1 brief sign-off; full options in
  `docs/M1-BRIEF.md`)
- **Options:** (A) one bounded re-attempt now, before any grid call — re-run
  `uv run m0.py pilot 20 qwen72b` once (~$0.06); completes → D8's tiers as written,
  green/amber → the D9 probe (~$0.01) and 72b joins M1's grid labeled in every table
  as a same-family, 10×-size substitution, never as the paper's qwen-7b;
  infrastructure-fails again → v1 closes two-model **permanently**, no further
  attempts in any later milestone. (B) defer the re-attempt to M2 — but a model
  joining then would have to backfill M1 cells after their gate was judged, splitting
  the judge-once discipline. (C) close two-model now, abandoning a 3/4-take pilot
  that $0.06 would finish.
- **Decision: A — one bounded re-attempt.** The roster freezes before the first grid
  call, whatever the outcome.
- **Why:** the only option that terminates the D12 thread today at known cost, and
  both outcomes are useful — a third family strengthens KICKOFF's "≥2 of 3", a clean
  close is honest. The success criteria are already satisfiable two-model, so this is
  upside, not need.
- **Outcome (2026-07-06, same session):** the re-attempt **completed cleanly** — no
  throttling this time — at **18/20 takes, D8 GREEN** (Wilson [70%, 97%]), measured
  $0.056. The D9 probe followed: **claim-3 NULL** — wrong emissions lossy 0/12 vs
  blank 0/12, every reply an abstention (Newcombe [−24%, +24%]), $0.002. So 72b is an
  abstainer at the wall like llama (deepseek remains the roster's only emitter), which
  affects claim 3 (M2), not claim 1. **72b joins the M1 grid**; the roster — llama,
  deepseek, qwen72b — is frozen in `m1.py`'s `ROSTER` constant (with a pinning test)
  for the whole milestone.

## D14 · Claim-1's "consistent with ~0": ceiling 0.10 with a pre-committed N-ladder

- **Date / decider:** 2026-07-06 / Kyle (M1 brief sign-off; full options + computed
  bounds in `docs/M1-BRIEF.md`)
- **Options:** operationalize KICKOFF claim 1's "lossy RR consistent with ~0" as a
  ceiling on the Wilson 95% *upper* bound, chosen together with the N schedule —
  (A) ceiling 0.10, judged at N=40, with D7's escalate-on-a-stray idiom;
  (B) ceiling 0.15 judged once at N=40, no escalation — cheaper, but a loose reading
  of the paper's 0.00 and a second smallness bar next to D7's 0.10;
  (C) no ceiling, judge the Newcombe gap alone — drops half the pre-registered claim.
- **Decision: A — ceiling 0.10 + the ladder.** Per lossy cell: run to N=20, stop for
  the **checkpoint** (hand-read ≥3 randomly picked trials against raw logs — the M0
  scoring lesson institutionalized — plus futility: ≥4 reclaims → not-cleared, stop;
  nothing can clear at 20, 0/20's bound is 16.1%). Extend to N=40 and judge: 0/40
  (bound 8.8%) clears; 1–3 reclaims → escalate **once** to N≈90, where ≤3 total
  reclaims clears (3/90 → 9.3%); ≥4 reclaims at any point is final — not-cleared
  (4/90 → 10.9%). source_first cells fixed at N=40, no ceiling; the Newcombe gap
  (source_first − lossy) is judged once, at final Ns. A model clears claim 1 only if
  both components hold at both g ∈ {0.1, 0.3}; v1 clears on ≥2 models of the final
  roster.
- **Why:** pre-commitment is worth most at the headline, where the temptation to bend
  would be strongest. One project-wide smallness scale (D7's ±0.10) instead of two; a
  stray reclaim neither kills the claim nor gets waved through — it buys a bigger
  sample, exactly like D7; and the checkpoint's only powers are bug-catching and
  futility stops, so the early look can never flatter the result. ≥4 lossy reclaims
  failing the gate is itself reportable structure (the paper says 0.00; we'd be
  measuring ≥10% — DISCREPANT territory for M3's table, not a shrug).

## D15 · Run evidence must survive the machine (+ two riders, both yes)

- **Date / decider:** 2026-07-06 / Kyle (M1 brief sign-off; full options in
  `docs/M1-BRIEF.md`)
- **Options:** (A) commit paid-run evidence per milestone — `runs/` stays gitignored
  as the working directory; each milestone's closing PR copies its JSONLs into
  `evidence/<milestone>/` and commits them (text JSONL, ~1 MB per milestone);
  (B) keep gitignored, archive manually — the convention that just left M0's
  evidence stranded on a single machine; (C) external storage (release assets /
  gist) — more moving parts than ~1 MB deserves.
- **Decision: A — commit evidence per milestone**, plus both riders: **(a)** commit
  `uv.lock` (standard for an application — pins the exact dependency versions runs
  used); **(b)** commit session-log *text*, gitignore media
  (`docs/session-logs/*.mp3` and kin — the ~4 MB M0 audio memo never enters git).
- **Why:** the methodology stands on auditable trials (per-trial gates, hand-read
  checkpoints); evidence that lives on exactly one machine — the near-miss this
  brief's remote drafting session exposed, when a fresh clone could see none of it —
  makes those guarantees unverifiable after the fact. The committed bank is also
  literally M2's input (D5's pairing made durable), so this is reproducibility and
  M2's substrate in one move. Executed at sign-off: M0's surviving JSONLs archived to
  `evidence/m0/` (70 files, ~460 KB), `uv.lock` committed, the M0 session-log text
  committed, media gitignored.
