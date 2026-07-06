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
