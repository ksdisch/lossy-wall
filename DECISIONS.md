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

## D16 · Claim 2's cell plan: both wall g × all three models vs M1's archived cells

- **Date / decider:** 2026-07-07 / Kyle (M2 brief sign-off; full options in
  `docs/M2-BRIEF.md`)
- **Options:** (A) six lossy_padded cells (3 models × g ∈ {0.1, 0.3}) at N=40 under
  D7's containment ladder (judge at 40; not contained → extend once to ≈90; final),
  judged against M1's archived lossy and source_first cells — judged once, zero
  re-runs — with the composition mirroring D14: a model clears claim 2 only if BOTH
  components (Newcombe on lossy_padded − lossy contained inside ±0.10; Newcombe on
  source_first − lossy_padded excludes zero) hold at BOTH wall g; one-g-only is
  PARTIAL; v1 clears on ≥2 of 3 models. (B) g=0.1 only — halves the padded spend but
  leaves "did padding rescue at 0.3?" unanswered against claim 1's both-g standard.
  (C) fresh lossy comparator arms alongside the padded cells — re-runs a judged
  condition on the same bank trajectories (only provider noise can differ), putting
  two numbers for one cell into the record.
- **Decision: A — both wall g, all three models, archived comparators.**
- **Why:** symmetric with the headline's composition (the control is not held to a
  weaker standard than the claim it protects), zero duplicated cells, and the
  composition is fixed before any data exists — the property that made D14 worth
  having. Known contingency, priced in the brief: a padded escalation on llama or
  qwen72b triggers a bank top-up first (≈$0.015 / ≈$0.16). No numeric futility
  shortcut exists for padded cells — the containment boundary depends on the
  comparator (4/90 fails against a 0/40 comparator at +10.9% but clears against
  deepseek's 1/90 at +9.8%) — so the ladder is the whole schedule and the
  checkpoint's power over these cells is the hand-read only.
- **Outcome (2026-07-07, M2 close):** **claim 2 CLEARED, 3 of 3 models** (bar ≥2).
  Every padded cell contained inside ±0.10, every separation ≥ +87.6% at the floor.
  Both pre-computed boundary cases fired and resolved exactly as written: deepseek
  padded@0.1 (1/40 vs its 1/90 comparator → escalate → 1/90, contained ±5.0%) and
  qwen72b padded@0.3 (1/40 vs 0/40 → escalate → bank top-up 40→90 taken ($0.174,
  the priced contingency) → 1/90, contained [−7.7%, +6.0%]). Both strays were
  hand-read lucky recoveries kept under strict scoring; contained sibling cells
  never re-touched. Verdict tables: `ROADMAP.md` M2.

## D17 · Claim 3's design: a new blank arm vs the archived lossy comparator, counted blind

- **Date / decider:** 2026-07-07 / Kyle (M2 brief sign-off; full options in
  `docs/M2-BRIEF.md`)
- **Options:** (A) blank cell at N=40 on deepseek, run over the same m1 bank in bank
  order; emission comparator = M1's archived deepseek lossy@0.1 rows (n=90), whose
  abstain-vs-emit split was deliberately left untallied when the rule was committed;
  counting rule = `grader.emitted_wrong` (wrong emission = `emit_attractor` or
  `emit_other_wrong`; abstain = no parsed ANSWER value or a hedge phrase, the
  author's rule verbatim); gate = the Newcombe 95% interval on wrong-emission
  (lossy − blank) excludes zero; both arms counted once, at judge time. (B) fresh
  lossy emission arm + blank arm, both N=40 in the same run — same trajectories
  anyway, duplicates a judged cell. (C) blank at N=20 — underpowers the
  pre-registered N≈40 to save about a penny. Rider (a): extend llama/qwen72b's
  claim-3 probe NULLs to N=40 (~$0.015, purely descriptive).
- **Decision: A — blank N=40 vs the archived comparator, counted blind; rider (a)
  NO** — the abstainers' probe NULLs stand as recorded verdicts, reported plainly
  per KICKOFF.
- **Why:** the pairing does the inferential work (same trajectories, same problems,
  same correction — only the note differs) and the blind commitment does the
  hygiene: the counting rule was fixed 2026-07-07 while the archived split was
  genuinely unknown, so the pre-registration can't have been shaped by the data.
  The design's one weakness — the two arms were sampled on different dates
  (temperature 0.0, same pinned models and routes) — is named in the record and
  reported with the result. No gate consumes a bigger abstainer null.
- **Outcome (2026-07-07, M2 close):** **claim 3 CLEARED on deepseek.** The archived
  split, counted once at judge time (blank at final N=40, enforced in code): lossy
  52/90 wrong emissions (33 attractor + 19 other-wrong, 37 abstains, 1 reclaim) vs
  blank 0/40 (40/40 abstains). Gap +58%, Newcombe [+44.2%, +67.5%] — excludes zero
  decisively. The blank replies were hand-read at the checkpoint (explicit declines,
  classified exactly as a human reads them). Abstainer nulls restated per rider (a):
  llama +1/12, qwen72b 0/12, not extended.

## D18 · The knob fills: N=40 uniform, all three models

- **Date / decider:** 2026-07-07 / Kyle (M2 brief sign-off; full options in
  `docs/M2-BRIEF.md`)
- **Options:** (A) lossy + source_first at g ∈ {0.6, 1.0} on all three models at
  N=40 with the standard N=20 checkpoint — descriptive cells (they gate nothing),
  Wilson bars on the committed figure, the sf@0.6 ≡ sf@1.0 replicate check riding
  along free. (B) N=20 descriptive-lite — halves M2's biggest line item, but a
  mid-range cell reads ±20+ points of mush and invites a mid-run extension. (C)
  deepseek only — two per-model panels go half-empty.
- **Decision: A — N=40 uniform, all three models.**
- **Why:** uniform N keeps every point on the capstone figure at the same
  evidential weight, and fixing the size now removes the mid-run "it looks
  interesting, extend it" call — the flexible-N researcher degree of freedom the
  project keeps closing off. If a knob cell lands mid-range (the wall's onset, the
  most interesting descriptive outcome), N=40 already resolves it. The absolute
  cost difference is dimes; the transcript cells dominate M2's spend either way.
- **Outcome (2026-07-07, M2 close):** deepseek and qwen72b at the ceiling in all
  four knob cells (40/40 each: lossy@0.6, lossy@1.0-transcript, sf@0.6, sf@1.0) —
  the curves converge above the source threshold as the protocol predicts. llama
  dips at high g (38, 28, 27, 26 of 40; sf replicate consistent −3%
  [−22.4%, +17.6%]); the targeted read attributes it to 600-token-cap abstains
  (rambling verification loops, no ANSWER line — several with the correct total
  computed mid-reply) plus genuine attractor re-emissions with the source in hand.
  Real behaviour, honestly read; carried as a caveat on the llama panel of
  `docs/figs/m2-knob.png`. N=40 uniform held — no mid-run extensions anywhere.

## D19 · The oracle run: their pilot, their defaults, the paper economy, on llama

- **Date / decider:** 2026-07-07 / Kyle (M3 brief sign-off; full options in
  `docs/M3-BRIEF.md`)
- **Options:** (A) the author's `run_pilot.py --real --fix --task arith` on
  llama-3.1-8b-instruct at their tool defaults — temperature 0.0 (= D10's sampling)
  and the full 32-problem × 3-seed paper economy, n=96 per (policy, g, arm) cell,
  ~4,896 calls ≈ $0.08–0.15, staged seed-1-smoke → checkpoint → `--seeds 3` resume;
  (B) the README cost-note economy (`--n 8`, n=24/cell, ~1,224 calls) — cheaper, but
  roughly double the agreement criterion's blind spot and no longer n-matched to the
  paper's tab:wall; (C) deepseek as the overlap model — points the one
  protocol-validation instrument at a cell where THEIR readout is known-suspect (the
  escaped-`\$` parser blindspot), so a disagreement couldn't tell our-protocol-drift
  from their-parser-bug. Rider (a): repeat the run at temperature 0.7.
- **Decision: A — paper economy on llama at their defaults; rider (a) NO.**
- **Why:** the author's own protocol at the author's own published cell size through
  the author's own unmodified code is the strongest form of D1's promise; sampling is
  matched to our archived cells by construction (their tool default = our D10); and
  the agreement criterion has real teeth at n=96 (boundary arithmetic pinned in the
  brief: it tolerates 8/96-scale noise, fires on a ≥ ~12-point structural shift). The
  0.7 rider would put a second oracle number on the same condition to buy the
  point-matching v1 never claims. Known trade-off, priced: their runner is serial and
  stays unmodified — ~2.5–4.5 h background wall-clock, resume-safe.
- **Outcome (2026-07-08, M3 close):** ran exactly as staged. Probe (<$0.001) → seed-1
  smoke (96 units, 1,632 calls, $0.018, 12,390s) → **the checkpoint held**: our
  recount matched their console cell-for-cell at 2 decimals both arms, the spot-check
  read 9/9 sampled rows internally consistent against the dumped truth/drift values,
  per-unit cost $0.0002 → `--seeds 3` resume (192 units, 3,264 calls, $0.037,
  14,782s). Full economy delivered: 288 units, 4,896 calls, n=96/cell, **$0.055
  measured** (envelope $0.08–0.15; ceiling untouched). The one estimate that missed
  was wall-clock: ~7.6h serial vs the 2.5–4.5h guess (slow provider day, 120–200s/unit
  measured) — cost unaffected, resume-safety never needed.

## D20 · The cross-check is a protocol-fidelity line, not a re-judging

- **Date / decider:** 2026-07-07 / Kyle (M3 brief sign-off; full options in
  `docs/M3-BRIEF.md`)
- **Options:** (A) per-claim verdicts stand as judged (judged-once); the cross-check
  adds a separate protocol-fidelity line — **AGREE** iff the Newcombe 95% interval on
  (their rate − ours) contains zero on all six wall-region overlap cells, else
  **DISCREPANT** + the pre-committed protocol audit (protocol diff first, readout
  recount second, cause or "unexplained" reported either way) — with the
  verdict-vocabulary mapping (REPRODUCED / PARTIAL / NULL / DISCREPANT) committed in
  the brief before the oracle run exists; (B) the cross-check gates the headline
  (REPRODUCED requires AGREE) — hands the author's harness, with two documented
  defects (broken table replay, parser blindspot), a veto over our verdict; (C) no
  pre-committed mapping — the researcher degree of freedom the project keeps closing.
  Rider (a): a pre-declared, $0, descriptive wrong-emission recount of the archived
  llama and qwen72b lossy@0.1 rows (n=40 each) so their tab:blank values get a
  same-protocol neighbor in the comparison table.
- **Decision: A — separate fidelity line, mapping pre-committed; rider (a) YES**
  (counted once at table time; gates nothing; the blank arms stay at probe n=12 —
  D17's declined rider stays declined).
- **Why:** the claim verdicts and the protocol-fidelity question measure different
  things — what our protocol found, and whether two independent builds of the
  protocol agree — and keeping them separate is what lets both be reported honestly.
  A DISCREPANT cross-check still lands in the README headline sentence with its audit
  finding, not in a footnote; it just cannot rewrite judged records.
- **Outcome (2026-07-08, M3 close):** **AGREE — all six intervals contain zero**
  (lossy@0.1 0/96 vs 0/40 [−8.8%, +3.8%]; lossy@0.3 1/96 vs 0/40 [−7.8%, +5.7%];
  padded 0/96 vs 0/40 both g; sf 96/96 vs 40/40 both g [−3.8%, +8.8%]). No audit
  fired. The fidelity line sits in the README headline beside the claim verdicts,
  which stand as judged. Rider (a) counted at table time: llama lossy@0.1
  wrong-emission 2/40 = 0.05 W[0.01, 0.17] — its interval contains their tab:blank
  0.17 — and qwen72b 1/40 = 0.03. The extraction also surfaced two labeling facts the
  table carries: the paper's tab:wall ran at temperature 0.7 (tool default 0.0 = our
  D10, so the oracle run stayed sampling-matched), and the paper v2 vs their README
  disagree in the last digit on three wall cells (footnoted; the paper's values win
  the paper column).

## D21 · bootstrap.py: the author's method verbatim, over every gated cell and gap

- **Date / decider:** 2026-07-07 / Kyle (M3 brief sign-off; full options in
  `docs/M3-BRIEF.md`)
- **Options:** (A) percentile bootstrap, B=5,000, seeded `random.Random(0)` — their
  `boot_ci` re-typed with attribution (D6's rule: reference, re-type, never import) —
  for every GATED cell rate and gap in claims 1–3, with independent two-arm
  resampling for differences (arms treated unpaired everywhere, D5/D14's
  conservative convention); appendix table beside Wilson/Newcombe; (B) claim-1 cells
  only — skips two of three claims gated on the same machinery; (C) every cell
  including the knob descriptives — decoration on cells that gate nothing.
- **Decision: A — every gated cell and gap.**
- **Why:** the appendix exists so a reader can check that the interval-method choice
  never drove a verdict, so it must cover exactly the verdict-driving numbers and
  nothing else. Wilson decided and still decides (D4); any disagreement is flagged
  and Wilson stands. The known 0/n degeneracy (every resample of 0/40 is 0/40, so the
  bootstrap interval collapses to [0.000, 0.000] — false certainty at the extremes)
  was named in the brief before any output existed; the appendix shows it as a taught
  result, which is itself the argument for D4.
- **Outcome (2026-07-08, M3 close):** appendix committed
  (`evidence/m3/bootstrap-appendix.txt`): 39 rows — exactly the gated cells and gaps
  of claims 1–3 — **zero Wilson-vs-bootstrap gate disagreements**, so the method
  choice never drove a verdict. The degeneracy showed on every all-zero cell as
  predicted. `boot_ci` re-typed verbatim with reference-stream tests pinning the
  exact RNG draws (test_bootstrap.py).

## D22 · The capstone: one composite figure

- **Date / decider:** 2026-07-07 / Kyle (M3 brief sign-off; full options in
  `docs/M3-BRIEF.md`)
- **Options:** (A) one `docs/figs/capstone.png` — knob curves per model (both
  policies, padded points, the blank point) + claim-3 emission bars + the cross-check
  comparison panel (ours vs their-run vs paper-committed on the llama wall cells) —
  built entirely from archived rows plus the oracle run, $0 new spend; (B) bless the
  M2 figure pair as the capstone — zero new code, but no single shareable image and
  the cross-check never gets visualized; (C) A without the cross-check panel.
- **Decision: A — the composite, cross-check panel included.**
- **Why:** v1's deliverable is one legible artifact; a capstone that needs three
  files and a paragraph of arrangement isn't one. The milestone figures
  (`m1-wall.png`, `m2-knob.png`, `m2-emission.png`) stay frozen as committed records.
- **Outcome (2026-07-08, M3 close):** `docs/figs/capstone.png` committed — knob
  curves per model with padded/blank points, the 52/90-vs-0/40 emission bars, and the
  cross-check panel with ours/their-run/paper visibly coincident on all six wall
  cells. $0; milestone figures untouched.

## D23 · M4 scope: the core soft-wall test (lean-first); cross-check + claim-3 layerable

- **Date / decider:** 2026-07-08 / Kyle (post-v1 fork + M4 brief sign-off; full options
  in `docs/M4-BRIEF.md`)
- **Fork context:** v1 closed (claims 1–3 REPRODUCED, cross-check AGREE, ≈$0.97); KICKOFF
  gated M4/M5 on "the effect shows" — it did — so the gate condition was met. At the fork
  Kyle picked **B (open M4, the logic family)** over A (close + /seed-hunt) and C (open M5);
  M5 stays gated-open.
- **Options (M4 scope):** (A) core — lossy / lossy_padded / source_first × g ∈ {0.1, 0.3} ×
  the frozen trio, read through the recov/inherit/novel/abst taxonomy, gated by D25, gated in
  turn by the D24 logic drift-take pilot; claim 3 descriptive via the inherit fraction;
  (B) core + one llama·logic cross-check cell through the author's harness (extends D1 to the
  new family, on the only anchored model); (C) B + a formally gated claim-3 blank/emission
  arm on a D24-confirmed logic emitter.
- **Decision: A — the core.** B and C left as clearly-priced arms, layerable later (incl.
  mid-milestone).
- **Why:** the guardrail is lean-first — no extra arm before the headline gap reads honestly
  — and M4's headline is the fix-generalizes gap plus the soft-floor characterization. The
  cross-check and formal claim-3 are real arms to layer once the core reads clean, exactly as
  M1→M2→M3 layered. A keeps M4 the thinnest falsification slice; both extensions stay
  sign-off-able add-ons.

## D24 · The logic drift-take pilot: run it per model before any grid (tiered like D8)

- **Date / decider:** 2026-07-08 / Kyle (M4 brief sign-off)
- **Options:** (A) a ~20-trial logic drift-take pilot per model, tiered as D8 (≥14/20 green;
  10–13 amber → recipe audit + 1/t̂ inflation; <10 trigger → the model sits out M4's grid,
  M4 proceeds on the takers and says so), with a disposition/taxonomy read alongside that
  doubles as the claim-3-on-logic powerability probe; no grid on a model until drift takes;
  (B) assume the arithmetic take transfers, skip the pilot.
- **Decision: A — run the pilot.**
- **Why:** the project's #1 riskiest assumption (drift must take) is unproven on logic, and
  logic is the likeliest place in the study for take to behave differently — a model can solve
  the puzzle in one step and refuse the planted clue (qwen-7b did exactly this on arithmetic,
  firing its D8 trigger). Cheap (~$0.02–0.05), decisive, and it front-loads the claim-3
  powerability question so D23-C becomes data-backed. B risks funding a full grid on a model
  that never took the plant — the failure M0 exists to prevent.
- **Outcome (2026-07-08, M4 pilot — ran, bug caught, roster settled two-model):** the pilot's
  first pass fired a **false 0/20 TRIGGER on llama** — the mandatory-checkpoint hand-read (the M0
  scoring lesson) traced it to a readout bug, not behaviour: `TAKE_PROBE_LOGIC` had been set equal
  to `FOLLOWUPS_LOGIC[6]` (the author's conversational restatement turn) and so never carried
  D11's format-explicit contract the arithmetic `TAKE_PROBE` has. llama answered the probe with a
  bare token ("Tom"); the strict author-verbatim `ANSWER:` parser returned None; 9 genuine
  drift-commits read `took=false`. The same take-probe path drives `run_bank`, so it would have
  silently failed to fill llama's bank too. **Fix** (branch `fix/m4-logic-take-probe-format`):
  `TAKE_PROBE_LOGIC` made format-explicit ("…State it as 'ANSWER: <word>'."), decoupled from
  `FOLLOWUPS_LOGIC[6]` (the session-1 follow-up stays verbatim), pinned tests updated — no parser
  change, strict-everywhere held. The `DriftFake` always emits a clean `ANSWER:` line, which is
  exactly why 222 green tests missed it (D11's standing caveat: fakes validate mechanics, not
  real-model format behaviour). **Final tiers under the corrected probe:** qwen72b **15/20 GREEN**
  (wall recov 11 / abst 4), deepseek **10/20 AMBER** (recov 7 / inherit 1 / abst 2), llama **9/20
  TRIGGER** (abst 9 — a pure abstainer at the wall). Cost: pilot $0.061 + llama re-pilot $0.002 =
  **$0.063 measured**.
- **Fidelity audit (D24/D8, run before banking):** our session-1 recipe confirmed faithful to the
  author's `experiment.py` — `plant` matches verbatim (`experiment.py:40-41`), `build_trajectory`
  mirrors their plant→follow-up-loop over `FOLLOWUPS_BY_KIND[kind]`, problems/follow-ups re-typed
  verbatim (D6). Decisive: deepseek and qwen took on the *same 20 problems*, so the recipe
  demonstrably induces takes — **llama's trigger is genuine model behaviour**, not our bug.
- **Roster (D13 frozen — trigger sits out, no swap):** llama **sits out M4's grid**; M4 proceeds
  **two-model, deepseek + qwen72b**, meeting KICKOFF's ≥2-of-3 bar (as v1's D12 two-model close
  did). deepseek runs under the **amber protocol** (recipe audit done; bank generation inflated by
  1/t̂ ≈ 2×; weak take noted in the README). Disposition read: **deepseek is the lone emitter
  candidate** (the only inherit in the trio at the wall); qwen recovers-or-abstains; llama
  pure-abstains — so a formal claim-3 (scope C) would ride on deepseek alone, its pilot inherit
  signal thin (1/10). Banking caveat: deepseek's take is **structure-dependent** (took all 10
  ordering puzzles, refused all 10 assignment ones — the assignment drift contradicts an explicit
  stated constraint), so its bank will skew toward ordering problems.
- **Anchor-out resolution (2026-07-08 / Kyle — resolves a D25 contingency left unspecified):**
  with llama (our only model with a published logic number) out, **scope B (the llama·logic
  cross-check) is moot**, and D25's REPRODUCED clause "on the anchored model (llama) our soft-wall
  shape matches the paper" is **not evaluable**. Kyle's call: the **≥2-model gap governs** the
  verdict; the anchor-shape clause is **reported as "not evaluable — anchor sat out,"** not a
  failure — v1's arithmetic cross-check (D20, AGREE) already validated our build independently.

## D25 · The soft-wall gates + verdict mapping: gap-gates claim 1, separation-gates claim 2

- **Date / decider:** 2026-07-08 / Kyle (M4 brief sign-off; computed bounds in
  `docs/M4-BRIEF.md`)
- **Context:** the wall is soft on logic (paper llama lossy 0.25/0.12 vs sf 0.67), so the
  arithmetic gates don't transfer — claim 1's lossy ceiling (≤0.10) is false-by-the-paper,
  and claim 2's equivalence (padded − lossy inside ±0.10) is **unpowerable at hobby N** on a
  mid-range rate (Newcombe [−0.19, +0.19] at N=40; ~N≥150/arm to close it).
- **Options:** (A) gate claim 1 on the **gap** (Newcombe sf − lossy excludes zero, both g)
  and REPORT the soft floor; gate claim 2 on **separation** (sf − padded excludes zero) and
  report the padded ≈ lossy overlap descriptively with the unpowerable-δ caveat; claim 3
  descriptive via the taxonomy (gated only under scope C); the recov/inherit/novel/abst
  taxonomy the standard readout, the ~1/k chance floor stated per cell; REPRODUCED / PARTIAL /
  NULL / DISCREPANT mapping pre-committed. (B) keep a lossy ceiling loosened to ≤0.30 + the
  gap — an arbitrary band with no paper basis. (C) gate on point-matching the paper — an
  explicit KICKOFF non-goal.
- **Decision: A — gap + separation + descriptive floor, mapping pre-committed before any
  data.**
- **Why:** the finding M4 reproduces IS "the fix generalizes AND the wall is soft on logic,"
  so the gate must test the fix (the gap, the half of claim 1 that transfers) and REPORT the
  softness, never demand a hard floor the paper itself disproves. Reuses v1's exact Newcombe
  instrument, adds no new smallness constant, and turns the one awkward statistic (mid-range
  equivalence) into a pre-registered, honestly-reported limitation instead of a bent gate.
  Verdict mapping: **REPRODUCED** = gap excludes zero both g on ≥2 models AND llama's
  soft-wall shape matches the paper within noise; **PARTIAL** = holds on some (model, g) but
  not the bar, or the shape diverges; **NULL** = no gap (fix doesn't generalize); **DISCREPANT**
  = scope B/C cross-check divergence → D20's protocol audit.

## D26 · N=60 flat for the soft wall, no escalation ladder (+ two riders, both yes)

- **Date / decider:** 2026-07-08 / Kyle (M4 brief sign-off)
- **Options:** (A) N=60 per cell, flat, with the N=20 hand-read checkpoint (bug-catch the new
  single-token readout first; futility a light note), judged once at 60; (B) N=40 (v1's
  economy); (C) N=90 flat (paper economy).
- **Decision: A — N=60 flat.**
- **Why:** the gap gates at N=40 already (computed), so N is bought for the DESCRIPTIVE soft
  floor: lossy 0.25 reads ±13 pt at 40, ±11 pt at 60, ±9 pt at 90 — diminishing returns past
  60. N=60 gives decisive gap power and a floor tight enough to characterize "how soft"
  without paying the paper's N=96 on every cell. No escalation ladder: nothing gates on the
  noisy floor, so fixing N (not laddering it) keeps the same anti-degree-of-freedom discipline
  v1 held.
- **Riders (recorded here, both YES):** (a) a verbatim arXiv v2 logic-table extraction, free,
  before judging (→ `evidence/m4/paper-extraction-logic.md`, `m4.PAPER` logic constants pinned
  by a test, README-vs-paper variance footnoted — mirrors M3); (b) adopt the recov / inherit /
  novel / abst taxonomy (re-typed from `logic_failmode.py`, D6) as the standard logic readout.
