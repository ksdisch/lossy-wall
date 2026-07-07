# Session wrap — lossy-wall: kickoff scaffold published
*2026-07-06 · repo: [ksdisch/lossy-wall](https://github.com/ksdisch/lossy-wall) (public) · session scope: scaffold only — no harness code, by design*

## 1. What we did

- Resumed the kickoff skill at its scaffolding step, off the approved brief at `~/Projects/_kickoffs/2026-07-06-lossy-wall.md`; the interview and consent gate were completed in a prior session — nothing was re-asked, no decision reopened.
- Created `~/Projects/lossy-wall/` and copied the brief **verbatim** to `docs/KICKOFF.md` (`cp` + `diff -q` verification).
- Wrote `CLAUDE.md` mirroring decay-pin's section shape: What this is / Where we are (M0 not started) / How to run / Methodology guardrails / "Working with Kyle" teaching standard (carried over intact) / Working conventions.
- Seeded root `DECISIONS.md` with the four gate-record decisions **D1–D4** in decay-pin's ledger format (Date/decider · Options · Decision · Why).
- Wrote `README.md`: one-liner, Why, the three v1 claims with their CI gates, status line, docs-spine pointers.
- Added the uv app stub: `pyproject.toml` (`package = false`; deps `openai` / `python-dotenv` / `matplotlib`; `pytest` as a dev group), `.env.example` with `OPENROUTER_API_KEY` only, `.gitignore` covering `.env`, `.venv/`, `runs/`.
- `git init -b main` → root commit `e431677` (7 files) → `gh repo create ksdisch/lossy-wall --public --source=. --push`; `main` tracks origin, working tree clean at session end (this wrap log is the only untracked file).
- Updated cross-session memory (project file + index): "scaffold pending" → "scaffolded; next = M0".

## 2. The why

- **Scaffold-only session via handoff (gate-then-execute).** The prior session's gate captured both the decisions (D1–D4) and the consent (paths, `git init`, public `gh repo create`), so this session executed mechanically. Separating deciding from executing keeps a fresh-context session from "improving" a settled contract. Rejected alternative: re-running any interview step — explicitly forbidden by the handoff.
- **Verbatim brief copy over re-render.** `docs/KICKOFF.md` is the in-repo copy of an approved contract; retyping or tidying would fork the source of truth. Accepted staleness: its header still says "scaffold pending" — the README carries the live status line. Pattern: single source of truth, mechanical copy + mechanical verification.
- **decay-pin as template, not a fresh design.** Third repo in the lineage: the docs spine (KICKOFF / DECISIONS / ROADMAP / LEARNING), the methodology-guardrails section, and the uv app conventions are already debugged by two prior projects. The teaching-standard section binds every session, so it carried over nearly verbatim. Tradeoff: template phrasing had to be adapted wherever it presumed decay-pin's specifics (forge-gap port → decay-pin port, new riskiest assumptions).
- **D1 pinned where the temptation lives.** "The author's `reclaim-eval` is a cross-check oracle only — never a dependency" is commented directly inside `pyproject.toml`'s dependency section, the exact spot a future session would type `uv add reclaim-eval`. Pattern: record a constraint at the point of likely violation, not only in docs.
- **DECISIONS.md seeded at scaffold time, not at M0.** The gate record compresses each decision to a line; expanding to ledger format now (options + why, drawn from the brief's own language — nothing invented) prevents archaeology later and gives M0 a worked example of the format.
- **pytest as a dev group despite decay-pin avoiding pytest.** The brief's tech stack names pytest for the validator suite — a recorded, deliberate divergence from decay-pin's standalone-script tests. Adding the group now means M0 never touches packaging. Flag: it's one line of config unused until M0, accepted because the approved stack names it.
- **Public at creation.** Kyle's explicit gate choice (portfolio artifact, matching decay-pin). Side benefit: the repo history shows the pre-committed contract *before* any results exist — good for the replication-credibility story.

## 3. Concepts and vocabulary

- **Brittle Memory (arXiv 2606.25449)** — the effect under reproduction: at a matched memory budget, a lossy note that keeps a wrong conclusion but drops its recomputable source makes the error uncorrectable; the model re-emits the stale value where an *empty* memory would abstain. Anchor: README one-liner, `docs/KICKOFF.md`.
- **Reclaim rate (RR)** — fraction of trials where the model, given a directed correction, actually corrects the previously planted wrong value. The paper's headline metric: ~0.00 for lossy at the wall vs 0.99–1.00 for source_first. Anchor: v1 claim 1.
- **Integrity knob (g)** — how much of the note's source content survives compression, swept over {1.0, 0.6, 0.3, 0.1}; "the wall" = g ≤ 0.3, where lossy RR collapses. Anchor: Scope section, claim 1.
- **Memory policies (lossy / lossy_padded / source_first / blank)** — the compared note-construction strategies at a matched character budget: conclusion-only, conclusion + filler to the budget, recomputable-source-first, and no note. Anchor: D2.
- **Length control (lossy_padded)** — the arm that separates "the note's *content* fails" from "the note is *short*"; claim 2 rides on it. Industry framing: controlling for a length confound. Exact padding mechanics deliberately parked to the M0 brief.
- **Wilson score interval** — a confidence interval for a single proportion; well-behaved at small N and rates near 0/1, unlike ±std. Anchor: D4 — decides every per-cell gate.
- **Newcombe interval** — a CI on the *difference* between two proportions, built from their Wilson intervals; decides every between-arm claim. Anchor: claims 1–3.
- **Equivalence margin (δ)** — a pre-committed bound for claiming "no meaningful difference": the interval must sit inside ±δ, because an interval that merely *includes* zero is not evidence of equivalence. Anchor: claim 2; δ gets set in the M-brief before any paid run.
- **Cross-check oracle** — the author's released harness (`reclaim-eval`, Apache-2.0), run on one pre-committed overlapping cell to check our independent build against theirs — never imported, never a dependency. Anchor: D1, the pyproject comment.
- **Anti-rig validator suite** — tests against a deterministic fake model that reclaims *only when source tokens are present*; a harness that can't reproduce the fake's known behavior 3/3 is broken or rigged. The author's harness passes 3/3; ours must too, before any paid run. Anchor: M0 plan, methodology guardrails.

## 4. Takeaways

1. **Separate deciding from executing.** Capture decisions *and* consent at an explicit gate; a later session then executes without reopening anything. Today ran end-to-end off a recorded gate with zero questions asked.
2. **Copy contracts; never retype them.** "Verbatim" is only true if it's mechanically true — `cp` + `diff -q`, not re-rendering from context. Today: `docs/KICKOFF.md`.
3. **Record a constraint where it will be violated.** A rule that lives only in a doc gets missed at the moment of temptation; D1's no-dependency rule sits as a comment inside pyproject's deps list.
4. **Port proven shapes for repo N+1.** Mirroring a debugged template (spine, ledger format, uv conventions) is faster *and* safer than fresh design — the effort budget goes to the experiment, not the scaffolding.

## 5. Suggested next moves

1. **M0 stage brief — `docs/M0-BRIEF.md` (Recommended).** Open the fit-pilot per the teaching rhythm: a plain-terms brief resolving the kickoff's parked open questions (note-template fidelity, trial independence, lossy_padded budget mechanics, session-2 frame) with options + recommendation, before any code. Recommended because it's the declared next step, everything downstream depends on those answers, and it costs $0. Effort: one focused session. First re-extract the paper cache if `/tmp` was wiped: `defuddle parse https://arxiv.org/html/2606.25449v2 --md -o /tmp/reclaim_paper.md`.
2. **M0 offline plumbing.** Port the OpenRouter client + `stats.py` from decay-pin; build the problems generator, note builder (pure functions), parser + anti-rig validator suite. All offline, $0, and gates every paid call. Effort: 1–2 sessions; depends on the M0 brief.
3. **First paid pilots.** Drift-take pilot (N≈10–20 × 3 models) + disposition probe (N≈12, blank vs lossy at the wall); arms the kill/swap triggers. Cheap (likely < $1) but strictly after 1–2.
4. **Spine hygiene.** This wrap log is untracked; commit it with the M0 PR so the session-logs convention declared in CLAUDE.md is actually honored in history. Trivial.

## 6. 30-second elevator version

Today was the kickoff session for lossy-wall, my third reproduce-and-measure project after forge-gap and decay-pin. It replicates a paper called "A Lossy Memory Is Worse Than an Empty One": when a memory system compresses notes down to conclusions and drops the recomputable source, a wrong conclusion becomes permanent — the model keeps repeating the stale value even when you directly correct it, while a model with no memory at all would just abstain. The thinking was done in a previous session — an interview produced an approved brief with four locked decisions — so today was pure execution: I scaffolded the repo from that contract. That's the brief copied in verbatim, conventions and methodology guardrails ported from decay-pin, a decision ledger pre-seeded with the four kickoff decisions, and a minimal uv Python stub, all in one root commit pushed to a new public GitHub repo. There's deliberately zero experiment code yet; next is Milestone 0, a cheap fit-pilot that checks the effect is even measurable on my three budget models before the full grid spends anything.

## 7. Active recall

1. What is the Brittle Memory claim, and why is "worse than an *empty* memory" the counterintuitive part?
2. The author's harness is released and installable — why build our own, and what role does theirs play (D1)?
3. Why do Wilson and Newcombe intervals decide the claim gates while the bootstrap is only an appendix (D4)?
4. What two assumptions could kill the project, and how does M0 test each of them cheaply?
5. What confound does the lossy_padded arm exist to kill, and which claim rides on it?

---
Try to answer each aloud before scrolling. Answer key below.

### Answer key

1. When a note keeps a conclusion but drops the source that could recompute it, a *wrong* conclusion becomes uncorrectable: given a directed correction, the model re-emits the stale value (reclaim rate ~0), because the note anchors the error while containing nothing to fix it with. A model with *no* note would abstain or recompute fresh — so the lossy memory underperforms not just a good memory but *nothing at all*. A source-first note at the same character budget stays fully correctable, which is what makes it a policy choice, not a capacity limit.
2. An independent build *is* the replication: it tests whether the paper's written protocol is complete enough to rebuild from — re-running the author's own code would only test that their code runs. Their harness serves two narrow roles: protocol reference while reading, and cross-check oracle on ONE pre-committed overlapping cell, with agreement or disagreement reportable either way (disagreement triggers a protocol audit). It is never imported by our harness code and never appears in `pyproject.toml`.
3. A reclaim rate is a proportion, and Wilson/Newcombe are purpose-built proportion intervals that stay honest at small N and rates near 0/1 — and they're the lineage's already-tested `stats.py`, ported near-verbatim. The bootstrap addendum exists only because the *paper* reports bootstrap CIs, so the comparison table can show both methods, labeled. Pre-committing "Wilson decides on disagreement, discrepancy reported" removes the freedom to quote whichever interval flatters the result.
4. (a) **Drift must take**: the metric conditions on the model first committing to the planted wrong value; a model that won't adopt it has no experiment. Tested by the M0 drift-take pilot (N≈10–20 per model) with a pre-committed per-model kill/swap trigger. (b) **The emission gap must be powerable at hobby N** on ≥1 answering model (deepseek expected, disposition +0.83 per the paper): tested by the M0 disposition probe (blank vs lossy at the wall, N≈12 per model) before any full grid spends.
5. The length confound: lossy notes are both less informative *and* shorter, so "lossy fails" could just mean "short notes fail." lossy_padded keeps lossy's content but pads to the matched character budget, so claim 2 ("content, not length") requires (lossy_padded − lossy) inside a pre-committed equivalence margin δ *and* (source_first − lossy_padded) excluding zero — padding changes nothing, adding *source* changes everything.
