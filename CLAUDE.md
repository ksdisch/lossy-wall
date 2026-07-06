# CLAUDE.md — lossy-wall

Project conventions and guardrails for working in this repo. Read this first each session.

## What this is

Reproduce and measure, at hobby scale, the **Brittle Memory** effect (arXiv 2606.25449):
at a matched memory budget, a lossy note that keeps a wrong conclusion but drops its
recomputable source makes the error uncorrectable — the model re-emits the stale value
where an *empty* memory would abstain — while a source-first note at the same budget
stays fully correctable.

**Source of truth: `docs/KICKOFF.md`** — the approved kickoff brief (scope, phased plan,
risks, gate record). Scope decisions there are settled; don't relitigate them. Headlines:
v1 is **arithmetic ledgers ONLY**, g ∈ {1.0, 0.6, 0.3, 0.1}, policies
**lossy / lossy_padded / source_first (matched char budget) + blank at the wall**,
**directed corrections only**; models are **llama-3.1-8b-instruct / deepseek-chat /
qwen-2.5-7b** via OpenRouter; the logic family and source-size boundary arm are **gated
post-v1**; the author's `reclaim-eval` package is a **cross-check oracle only — never
imported by our harness code, never in `pyproject.toml`** (D1).

The honest framing, always: *reproduced and measured a published finding — here is the
narrow, measured slice.* Never "I invented this."

## Where we are

**Current milestone: M0 — the fit-pilot** (not started; the repo is a fresh scaffold).
Port plumbing from decay-pin (OpenRouter client, `stats.py`); build the problems
generator, note builder (three policies + blank as pure functions), answer-line parser +
emission classifier, and the anti-rig validator suite (3/3 green on the deterministic
fake); then the drift-take pilot (N≈10–20 × 3 models) and the disposition probe (N≈12,
blank vs lossy at the wall); model pings + measured cost. Author's package goes into an
isolated venv; their free DryRun probe + `reproduce_tables.py` run for reference ($0).

**Riskiest assumptions — keep them front-of-mind:**
1. **Drift must take** — reclaim rate conditions on the model first committing to the
   planted wrong value. No take → no experiment on that model. Kill/swap trigger per
   model, armed in M0.
2. **The emission gap must be powerable at hobby N** on ≥1 answering model (deepseek
   expected). The M0 disposition probe answers this before any full grid spends.

## How to run

- Setup: copy `.env.example` to `.env` and put in a real `OPENROUTER_API_KEY` (gitignored).
- Anything: `uv run <script>` — `uv` (Python 3.11+) manages the venv and installs deps on
  first run. This is an application, not a package (`package = false`).
- No harness code exists yet; building starts at M0.

## Methodology guardrails (load-bearing — do not drift)

- **Judge-free scoring, never an LLM judge.** Exact-match on a parsed answer line plus a
  mechanical abstain-vs-emit classifier. Parsing is where silent scoring corruption lives
  (the paper's v2 fixed its own parser bug): parser unit tests + the anti-rig validator
  suite (a deterministic fake that reclaims only when source tokens are present) must be
  green before any paid run.
- **Per-trial source-absence verification.** A note only counts as lossy if the
  recomputable source is demonstrably absent — a mechanical token test on the note, every
  trial (decay-pin's string-search-gate philosophy).
- **Wilson CIs on cells + Newcombe CIs on differences decide every gate** (D4); the
  bootstrap appendix is robustness only — on disagreement Wilson decides and the
  discrepancy is reported.
- **N ≥ 20 per cell**, scaling toward ~40–50 where CIs are wide. The binding constraint
  is the **statistics (noise floor), not the code or the cost.**
- **A cell whose CI overlaps its neighbor is not a result** — report it as a null/small
  effect, honestly. Each headline claim has an explicit CI gate in `docs/KICKOFF.md`; a
  claim that doesn't clear its gate doesn't get made. Equivalence (claim 2) needs its
  margin δ pre-committed in the M-brief before any paid run.
- **Direction + structure, never point estimates.** Zero Anthropic/OpenAI spend in v1.
- **Build the ugliest end-to-end version first**, then layer arms one at a time — M0's
  pilots prove drift takes and the gap is powerable before any full grid spends tokens.
- Record `temperature` (don't chase determinism via temp 0 — get signal from N).

## Working with Kyle — teaching standard + per-stage rhythm (load-bearing)

Kyle is driving this project to learn it deeply (it may become his career) and is sharp
but **new to coding jargon** — no CS degree. The job isn't just to ship code; it's to
leave him able to *defend every decision*. These rules bind **every session and tab**.

- **Explain-clearly standard.** Plain English first; define **every** jargon term the
  first time it appears, inline; **clearer, not longer** (the simplest accurate
  explanation, not the most exhaustive). If something stays fuzzy, that's a bug in the
  explanation — fix it.
- **Decision-brief format.** For any real choice, don't just pick — lay out 2–3 options
  in plain terms, each with its trade-off, plus your recommendation *and the reason*.
  Kyle decides or signs off; clear options are what make weighing in possible.
- **Per-stage rhythm (the docs spine).** *Start of a stage:* write the plain-terms brief
  + the real options into `docs/` before coding. *End of a stage:* update `ROADMAP.md`
  (status), append the choice to `DECISIONS.md` (options + why), add the teaching note +
  new words to `LEARNING.md`, and ask 3 recall questions. Raw blow-by-blow goes to
  `docs/session-logs/` via `/wrap`. **The spine beyond `KICKOFF.md` doesn't exist yet by
  design** — it starts with M0's start-of-stage brief; until then the repo holds only
  `docs/KICKOFF.md` plus the pre-seeded root `DECISIONS.md` (the kickoff's D1–D4).
- **Definition of done (keeps the spine fresh).** Once the spine exists, a stage isn't
  finished until its spine updates are committed in the **same PR** as the code.

## Working conventions

- **Teach while building.** After non-trivial code, explain what/why in plain English and
  define any jargon — see "Working with Kyle" above.
- **Keep it lean.** No premature abstractions, no extra arm before the headline gap reads
  honestly. Scope is one legible deliverable, not breadth.
- **Secrets:** never print or commit the `.env` value; only `.env.example` is tracked.
- Conventions beyond decay-pin's ported standard: TBD as the harness takes shape.
