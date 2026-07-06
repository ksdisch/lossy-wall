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
