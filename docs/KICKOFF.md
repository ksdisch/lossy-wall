# Kickoff Brief — lossy-wall
*Created 2026-07-06 · status: approved (scaffold pending — handoff to fresh session)*

## One-liner
Reproduce and measure, at hobby scale, the **Brittle Memory** effect (arXiv 2606.25449): at a matched memory budget, a lossy note that keeps a wrong conclusion but drops its recomputable source makes the error uncorrectable — the model re-emits the stale value where an *empty* memory would abstain — while a source-first note at the same budget stays fully correctable.

## Why now / the problem
decay-pin closed 2026-07-06 (D21); this is the third rung of the reproduce-and-measure lineage (forge-gap → decay-pin), picked the same day via `/seed-hunt` from a 1,600-paper sweep. It cleared the bar because: the deltas are enormous (RR 0.00 vs 0.99–1.00 at the wall); scoring is judge-free exact-match; source-absence is verified per trial by a token test on the note (the same string-search-gate philosophy decay-pin ran on); the cure is training-free (a compression-policy choice); and the paper's own primary model is an 8B cheap model — hobby scale is the paper's *native* scale, not a compromise. It's live: compress-toward-the-conclusion is what shipped memory systems do today. And it's a single-author, unreplicated, 1-star paper — a careful independent replication is genuinely useful, and **a null is pre-committed as a reportable verdict**. Kinship with decay-pin (compaction evicting a rule ↔ compression evicting a value's provenance) was weighed at seed-hunt and accepted.

## Who it's for
Kyle — learning + portfolio artifact. The decay-pin teaching standard binds every session: plain English, every jargon term defined, decision briefs for real choices, docs spine, recall questions. Today's alternative: nothing — decay-pin is closed.

## What success looks like
- **v1 done means** (observable, all under pre-committed gates, on ≥2 of 3 models unless stated):
  1. **The wall:** at wall integrity (g ≤ 0.3), lossy RR's Wilson CI consistent with ~0 *and* the Newcombe interval on (source_first − lossy) excludes zero.
  2. **Content, not length:** at the wall, (lossy_padded − lossy) within a pre-committed equivalence margin (δ set in the M-brief before any paid run, decay-pin D11 style) *and* (source_first − lossy_padded) excludes zero.
  3. **Worse than empty** (the title claim), on ≥1 disposed-to-answer model (deepseek expected): Newcombe interval on wrong-emission rate (lossy − blank) excludes zero. On abstaining models the predicted null is reported plainly.
  - Plus: the g-sweep wall figure, README story, a comparison table (our Wilson CIs beside the paper's bootstrap CIs, labeled), current docs spine, and the **cross-check cell** — our harness vs the author's on one overlapping cell, agreement or disagreement reported either way.
- **Would be amazing:** all 3 models; the gated logic family lands (task-generality); the gated boundary arm lands ("we reproduced where the fix *fails*"); a capstone figure that travels.
- **Explicitly NOT trying to:** match point estimates (direction + structure only); invent mechanisms; use an LLM judge; benchmark memory products; claim anything about frontier models (zero Anthropic/OpenAI spend in v1).

## Scope
**In (v1):**
- ONE task family: **arithmetic ledgers** (the hard wall), problems generated in-repo.
- Integrity knob **g ∈ {1.0, 0.6, 0.3, 0.1}**; wall cells first, knob filled in later.
- Policies **lossy / lossy_padded / source_first** at matched character budget, **+ blank** at the wall.
- **Directed corrections only.**
- THREE models via OpenRouter: **llama-3.1-8b-instruct** (paper-primary; comparability + cross-check anchor), **deepseek-chat** (disposition +0.83; carries claim 3), **qwen-2.5-7b** (middle point, second family).
- The **cross-check stage** against the author's released harness, one overlap cell.

**Out / deferred / never:**
- **Gated (post-v1, only if the effect shows):** logic family (soft wall, task-generality); source-size boundary arm (the falsification stage).
- **Never (v1):** deployed systems (LangChain/mem0/vector), MultiWOZ, cascade, prevalence audit, adversarial battery, 8-model disposition sweep, frontier replay, single-conversation anchoring table, the one-prompt auto-distiller. No novel mechanisms. No LLM-judge grading, ever.

## Shape
CLI harness of `uv run` Python scripts + matplotlib PNGs — decay-pin's shape ported: OpenRouter client generalized, problems generator, note builder (the three policies + blank as pure functions), answer-line parser + emission classifier, N-trial runner with per-trial source-token verification, `stats.py` (Wilson/Newcombe) near-verbatim + a small bootstrap addendum.

## Inputs & data
No external datasets (problems are generated; MultiWOZ is out). Live input: OpenRouter responses. The author's harness (Apache-2.0, installable, replays its tables with no API key) as protocol reference + cross-check oracle — **never imported by our harness code**.
References: paper https://arxiv.org/abs/2606.25449 (HTML v2: https://arxiv.org/html/2606.25449v2); harness https://github.com/collapseindex/reclaim-eval.

## Integrations & dependencies
OpenRouter key (in hand). `uv` toolchain. GitHub **public** repo (Kyle's explicit choice at the gate, matching decay-pin). Author's package installed in an isolated venv for the cross-check stage only.

## Constraints
Hobby budget: full v1 grid ≈ 3 models × (~24 session-1 trajectories + ~400–500 session-2 calls) — likely **under $10** at these models' prices; the binding constraint is **statistics, not cost** (N≥20/cell scaling toward 40–50 where CIs are wide). Evenings-scale. Teaching standard throughout.

## Riskiest assumptions & unknowns
1. **Drift takes reliably on our roster** (RR conditions on the model first committing to the planted wrong value). — *cheap test:* M0 drift-take pilot N≈10–20/model; **kill/swap trigger per model.**
2. **The emission gap is powerable on ≥1 model at hobby N** (deepseek's +0.83 says yes; dispositions can shift under model updates). — *cheap test:* M0 disposition probe, blank vs lossy at the wall, N≈12/model, before any full grid.
3. **Answer parsing is clean** — the paper v2 fixed its *own* parser bug; exact-match + abstain-vs-emit classification is where silent scoring corruption lives. — *cheap test:* parser unit tests + an anti-rig validator suite (deterministic fake that reclaims only when source tokens are present — theirs passes 3/3, ours must too) + dry-run verdicts on wrong-arm data, all before paid runs.
4. **Our independent build matches the protocol** (note templates, g mapping, budget matching). — *cheap test:* the cross-check cell; disagreement triggers a protocol audit and is reportable either way.

## Open questions
- Note-template fidelity: paper's templates verbatim vs paraphrase — M0 brief, from App. A + their `problems.py`.
- Trial independence: fresh generated problem instances per trial (leaning yes; Wilson assumes independence) vs the paper's 8-problems × 3-seeds reuse — M0 brief.
- `lossy_padded` budget-matching mechanics (chars, per the paper) — M0.
- Claim 2's equivalence margin δ — pre-committed in the M-brief before paid runs.
- Model IDs/pricing/availability on OpenRouter — M0 ping.
- Exact session-2 frame ([system, note, correction] composition) — M0, from §3.2 + their `experiment.py`.

## Phased plan
### Milestone 0 — De-risk: the fit-pilot
Port plumbing (client, stats); build problems generator, note builder, parser, and the validator suite (3/3 anti-rig checks green on the deterministic fake); drift-take pilot (N≈10–20 × 3 models); disposition probe (N≈12, blank vs lossy at wall); model pings + measured cost. Install their package; run their free DryRun probe + `reproduce_tables.py` for reference ($0). Kill/swap triggers armed.
### Milestone 1 — The wall (thinnest valuable slice)
lossy vs source_first at g=0.1 and 0.3, directed, surviving models, N≥20→40 with a pre-committed escalation rule. Gate claim 1. Wall figure.
### Milestone 2 — The controls that make the claim
lossy_padded arm (claim 2, δ pre-committed) + blank arm with emission scoring (claim 3) on the disposed model(s); fill g=1.0/0.6 for the knob figure.
### Milestone 3 — Cross-check + capstone
Author's harness on the overlap cell; comparison table (Wilson vs bootstrap, labeled); capstone figure; README story; spine close-out. Verdict vocabulary pre-committed: REPRODUCED / PARTIAL / NULL / DISCREPANT — all reportable.
### Milestone 4 (gated) — Logic family
Headline cells on one model (task-generality; decay-pin M3 pattern).
### Milestone 5 (gated) — Boundary arm
Source-size sweep, one model: source_first cliffs past its budget — reproducing where the fix fails.

## Tech stack
Python 3.11+ / `uv`, minimal OpenRouter client, matplotlib, pytest for validators — decay-pin's stack verbatim (the point is porting a proven harness shape, not new plumbing). `stats.py` ported + small `bootstrap.py` for the robustness appendix.

## Gate record (2026-07-06)
Brief approved by Kyle; stress-test offered and skipped. Slug **lossy-wall**, stack confirmed, visibility **public** (explicit choice, matching decay-pin). Scaffolding delegated to a fresh session via /handoff — Kyle's consent to create `~/Projects/lossy-wall/`, the git repo, and the public GitHub repo `ksdisch/lossy-wall` was given at this gate. Kickoff decision seeds for the repo's DECISIONS.md: **D1** harness = build-in-repo + one pre-committed cross-check cell vs the author's released harness (reference-only otherwise); **D2** v1 scope cut as above; **D3** model roster = paper trio; **D4** stats = Wilson/Newcombe deciding gates + bootstrap robustness appendix (Wilson decides on disagreement, discrepancies reported).
