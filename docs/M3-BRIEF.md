# M3 Start-of-Stage Brief — cross-check + capstone

*Written 2026-07-07 · status: **signed 2026-07-07** — D19-A (rider a: no), D20-A (rider
a: yes), D21-A, and D22-A picked by Kyle and recorded in `DECISIONS.md`; the build may
start · scope source of truth: `docs/KICKOFF.md` (Milestone 3) · format follows
`docs/M2-BRIEF.md`.*

## What M3 is, in plain terms

M0–M2 measured everything v1 set out to measure: claim 1 (the wall) CLEARED 3 of 3
models, claim 2 (content, not length) CLEARED 3 of 3, claim 3 (worse than empty) CLEARED
on deepseek with the two abstainers' predicted nulls reported plainly. M3 measures
**nothing new on our harness** — every cell of ours is an archived, judged-once record.
M3 is the closing stage, four deliverables:

1. **The cross-check cell (the one paid item).** D1's promise, made at the kickoff gate:
   our harness was built independently from the paper's description, and one overlapping
   cell gets run through the **author's own released harness** (`reclaim-eval`) so the two
   builds can be compared on the same ground — agreement or disagreement reportable either
   way. This is what makes the project a *replication* (an independent rebuild that tests
   whether the paper's protocol description is complete enough to reproduce from) rather
   than a re-run of someone else's code. The author's package is the **oracle** here — a
   trusted external reference we compare against but never import (D1's wall: it lives in
   a sibling clone at `~/Projects/reclaim-eval/` with its own venv, never in our
   `pyproject.toml`).
2. **The paper-comparison table.** Our measured numbers beside the paper's committed
   numbers, every column labeled with its method (Wilson vs bootstrap), its n, its
   sampling, and its problem economy — KICKOFF's "our Wilson CIs beside the paper's
   bootstrap CIs, labeled." Plus the two protocol findings M0 already banked: their
   `reproduce_tables.py` exits nonzero on the public repo (empty `data/results/` — the
   "every table reproduces from committed results" claim fails on the artifact as
   shipped), and their answer parser shares the escaped-`\$` blindspot our M1 hand-read
   caught (confirmed in their current source; made mechanical by a free fixture check
   below).
3. **`bootstrap.py`, the robustness appendix.** D4's promised second opinion: the paper
   reports **bootstrap** confidence intervals (intervals built by *resampling* — redrawing
   the observed trials with replacement thousands of times and reading the spread of the
   resampled rates), so we compute bootstrap intervals with the author's exact method over
   our own gated cells and print them beside the Wilson/Newcombe intervals that decided
   every gate. Wilson decided and still decides (D4); the appendix exists so the
   methods comparison is honest, not to reopen any verdict.
4. **The capstone: figure + README story + spine close-out.** One figure that carries the
   whole result, a README rewritten around the pre-committed verdict vocabulary
   (REPRODUCED / PARTIAL / NULL / DISCREPANT — all four reportable, per KICKOFF), and the
   docs spine closed out. After this PR, v1 is done.

## What M0–M2 settled that M3 stands on

- **Every claim is judged; nothing re-runs.** All our cells are archived comparators under
  the judged-once rule (D14): llama lossy@0.1 0/40, lossy@0.3 0/40, padded 0/40 at both g,
  sf 40/40 at both g; deepseek's and qwen72b's tables likewise (`ROADMAP.md` M1/M2). M3's
  only paid trials run through the **author's code**, not ours.
- **The oracle is already installed and probed ($0, M0).** The clone at
  `~/Projects/reclaim-eval/` has its own `.venv` (D1's wall stays physical). Its free
  DryRun probe (`python -m reclaim.probe`) agrees with our deterministic fake's shape
  (source_first correctable, lossy/padded uncorrectable-silent, blank uncorrectable-loud);
  its `reproduce_tables.py` **passes its three correct-by-construction generator
  validators, then exits nonzero** because the public repo ships an empty
  `data/results/` — a recorded M0 finding that M3 reports.
- **Their parser carries the escaped-`\$` blindspot (ROADMAP's † note), now source-confirmed.**
  Their `llm.py::parse_answer` tolerates markdown/quote wrappers and a literal `$` before
  the value, but its wrapper set has no backslash — `ANSWER: \$197` (deepseek's LaTeX
  habit, roughly a third of its ANSWER lines in our M0/M1 evidence) parses to None, i.e.
  reads as an abstention. Harmless where the metric is reclaimed-vs-not (their own v2
  parser-fix note documents that logic); it bites exactly where a failure is decomposed
  into abstain-vs-emit — their disposition/blank tables. A free fixture check below makes
  this mechanical and reportable.
- **Sampling is matched by construction.** Their `run_pilot.py --fix` defaults to
  temperature 0.0 / max_tokens 600 — the same `llm.py` defaults our D10 pinned. So an
  oracle run at their tool defaults is sampling-matched to our archived cells with zero
  new decisions. (Their README's Findings header says the original core sweep ran
  temperature 0.7; the free paper-extraction task checks what the paper states for the
  wall table and the comparison table labels every column's temperature either way.)
- **Their trial economy is theirs, and it differs from ours in two labeled ways.** (1)
  Their arithmetic set is 32 fixed problems (8 canonical + 24 machine-generated,
  generator-validated) × 3 seeds = n=96/cell, the paper's tab:wall economy; ours generates
  a fresh problem per trial (D5). (2) Their runner rebuilds session 1 **per policy** (one
  unit = 1 drift + 8 commitment + 8 reclaim calls = 17 calls), so their policy comparison
  carries trajectory noise our D5 pairing removed. Both are protocol-faithful on their
  side; the table labels both.
- **What their logs can and cannot support.** Their checkpoint rows
  (`data/results/fix_*.jsonl`, resume-aware) log the parsed answer and the correct flag
  per (seed, problem, policy, g, arm) — **not the raw reply text, and not the
  temperature**. So verification on their run is recount + consistency checks (their
  problems are fixed with known truth and drift values), not our per-reply hand-read; the
  run's console log (which echoes config and measured cost) is captured to evidence as
  the config record. Our hand-read discipline lives where our readouts live — and M3 adds
  no new readouts: their rows arrive pre-scored by their code, which is the point of an
  oracle.
- **Evidence discipline extends to the oracle run (D15).** Their checkpoint JSONL, both
  console logs, and the fixture-check output are copied into `evidence/m3/` in the closing
  PR, key-scan clean.

## The design: one oracle run, three free deliverables

**The oracle run** (D19): from their clone, with their venv and our OpenRouter key in
their `.env` (their `.env.example` pattern; the key is never committed anywhere):

```
cd ~/Projects/reclaim-eval
.venv/bin/python scripts/run_pilot.py --real --fix --task arith \
  --model meta-llama/llama-3.1-8b-instruct --seeds 1     # smoke: seed 1 only
# ... the M3 checkpoint (below) ...
.venv/bin/python scripts/run_pilot.py --real --fix --task arith \
  --model meta-llama/llama-3.1-8b-instruct --seeds 3     # resume: pays only seeds 2-3
```

Their `--fix` mode runs lossy / lossy_padded / source_first over all four integrities and
**both correction arms** in one pass (that's their unit's anatomy; we do not modify their
code, so the generic-arm rows ride along and are reported as reference-only — our own paid
cells are directed-only by D2, so those rows have no counterpart and gate nothing).
Default economy: 32 problems × 3 seeds = **n=96 per (policy, g, arm) cell** — the paper's
tab:wall economy — at 288 units × 17 calls = 4,896 calls, checkpointed per unit and
resumable after any crash. llama is the overlap model: it is the paper's primary model and
the cross-check anchor D3 named on day one, and it is the roster's cheapest and least
parser-exposed (zero escaped-`$` replies in all our archived evidence).

**The overlap cells:** llama · arithmetic · directed × {lossy, lossy_padded, source_first}
× g ∈ {0.1, 0.3, 0.6, 1.0} = 12 cells. The **six at wall g (0.1, 0.3) are the gated set**
the agreement criterion judges against our six archived llama comparators; the six
knob-region cells (0.6, 1.0) are descriptive in the table, D18's pattern. Their g=1.0
lossy cell is the same transcript special case ours is — their runner is where we ported
it from.

**The free deliverables, before any paid call:**

- **`bootstrap.py` + tests (D21).** The author's interval method, re-typed (D6's rule:
  read their code as reference, re-type with attribution, never import): percentile
  bootstrap, B=5,000 resamples, seeded `random.Random(0)`, 95% read at the sorted 2.5/97.5
  quantiles — their `boot_ci` in `analyze_realworld.py` / `integrity_table_ci.py`
  verbatim. Cell rates resample that cell's 0/1 outcomes; differences resample each arm
  independently (our arms are treated unpaired everywhere, D5/D14's conservative
  convention). One known behavior named now, before any output exists: a percentile
  bootstrap of an all-zero cell is **degenerate** — every resample of 0/40 is 0/40, so the
  interval collapses to [0.000, 0.000], which is exactly the false-certainty failure mode
  proportion intervals exist to avoid. The appendix will show it on our 0/40 cells and say
  so; it is why D4 made Wilson the decider.
- **`m3.py` + `test_m3.py`.** Readers for our archived evidence and their `fix_*.jsonl`
  schema; the agreement judge as a **pure function with the boundary arithmetic pinned by
  tests** (the D14/D16 pattern — the verdict rule is in code before any data exists); the
  pre-declared descriptive recount (D20 rider a); the comparison-table builder; the
  capstone figure subcommand. Full pytest + anti-rig suite green before the oracle run.
- **The fixture check on their parser ($0).** A tiny script placed in *their* clone, run
  with *their* venv (the D1 wall: their code never runs inside our repo), feeding their
  `parse_answer` the escaped-`\$` reply strings from our archived deepseek evidence plus
  plain controls. Expected: their parser returns None (abstention) on `ANSWER: \$197`
  where ours reads 197.0. Output captured to `evidence/m3/`. The honest scope of the
  finding: it proves the **mechanism** in their current code; whether it moved their
  published deepseek/qwen numbers is unknowable from their committed artifacts (no raw
  replies), so the table footnote says "may under-read escaped commits as abstentions" —
  and since an under-read on the lossy arm can only shrink a lossy−blank emission gap,
  their deepseek Δ+0.83 would be a floor, not an artifact, if it bit at all.
- **The paper-number extraction ($0).** From the arXiv HTML (v2) and their README: the
  tab:wall llama arithmetic row (lossy 0.00/0.00 · padded 0.00/0.00 · source_first
  0.96/1.00 at g=0.3/0.1, n=96, with the paper's bootstrap CI brackets), the
  disposition/blank rows claim 3 compares against (deepseek Δ+0.83, qwen-2.5-7b +0.39,
  llama +0.17, the four frontier abstainers at 0.00 — the post-v2-correction values), and
  the paper's stated sampling config for those tables. Every extracted number lands in the
  comparison table with a citation.

**The comparison table** (D20): one row per compared cell, three number columns —
**paper-committed** (their published value + bootstrap CI, n=96) · **their-harness-run**
(the oracle run's raw outcomes, recounted by us — Wilson and their own boot_ci both
computable from their per-row logs) · **ours** (archived, Wilson, n=40–90) — plus label
columns: method, n, temperature, problem economy, arm. Claim-3 rows carry the extra
honesty labels: our deepseek gap (+58% [+44.2, +67.5], n=90/40, fresh problems, temp 0.0)
beside their Δ+0.83 (n=96, their problems, their sweep config); our llama probe NULL
(+1/12 vs 0/12, n=12/arm — underpowered by pre-commitment, D17 rider a declined) beside
their llama +0.17, with the concordance note that our probe interval already contains
their value; and their qwen-2.5-7b +0.39 labeled **no comparable cell** (our slot runs the
72b, a 10×-size same-family substitute — D13's standing label, never presented as the
paper's model).

**The capstone** (D22): `docs/figs/capstone.png`, one self-contained figure — the knob
curves per model (both policies, padded points and the blank point at the wall), the
claim-3 emission bars, and the cross-check panel (ours vs their-run vs paper-committed on
the llama wall cells) — assembled entirely from archived rows plus the oracle run, $0.
`m1-wall.png` / `m2-knob.png` / `m2-emission.png` stay untouched as milestone records. The
README story is rewritten around the verdict table; the spine closes out in the same PR.

## The gates, mechanically

**The cross-check agreement criterion (the only new gate in M3)** — pre-committed here,
before the oracle run exists:

- **Per cell**, for each of the six gated-region overlap cells: the Newcombe 95% interval
  on (their rate − our archived rate), our `stats.py`, unequal n as always (D14
  precedent).
- **Verdict:** all six intervals contain zero → **AGREE**. Any interval excludes zero →
  **DISCREPANT**, naming the cell(s), and the pre-committed audit runs: protocol first
  (diff their note string, session-2 frame, and correction wording against ours for the
  discrepant cell — all were re-typed verbatim in M0, so any drift is findable), readout
  second (recount their rows for that cell by hand), then report the cause or report
  "unexplained." Both outcomes are reportable (KICKOFF: "agreement or disagreement
  reported either way"); disagreement is a finding, not a failure.
- **Boundary arithmetic** (computed with our `stats.py` against our archived llama cells,
  at the n=96 economy): theirs 0/96 vs ours 0/40 → [−8.8%, +3.8%], consistent; theirs
  4/96 vs 0/40 → [−5.0%, +10.2%], consistent; even 8/96 vs 0/40 → [−1.3%, +15.6%], still
  consistent (the criterion deliberately tolerates provider noise and stray
  lucky-recoveries at the extremes); their published sf@0.3 value 0.96 ≈ 92/96 vs our
  40/40 → [−10.2%, +5.0%], consistent; sf 84/96 vs 40/40 → [−20.6%, −2.3%], **fires**. So
  the gate ignores noise and catches structure: a ≥ ~12-point source_first drop or a
  comparable lossy rise on their side is what DISCREPANT means.
- **The knob-region overlap cells gate nothing** (descriptive, D18's rule), and their
  internal wall structure (their own sf−lossy gap at wall g) is reported as a descriptive
  number, not a gate — our comparators already encode the structure, so a second gate
  would be redundant.

**The verdict vocabulary mapping (D20)** — committed before the oracle run, so the README
cannot be shaded after it:

| verdict word | rule (mechanical) | where v1's claims sit under it today |
|---|---|---|
| **REPRODUCED** | the claim's pre-registered gate cleared at its pre-registered bar | claims 1, 2 (3/3 vs bar ≥2/3); claim 3 (deepseek, bar ≥1 disposed model; abstainer nulls are the paper's own predicted behavior, reported plainly) |
| **PARTIAL** | gate cleared below the bar, or one-g-only composition | — |
| **NULL** | gates judged, no effect at the pre-registered margins | — |
| **DISCREPANT** | a measured result contradicting the paper's direction/structure (e.g. lossy RR ≥ 10% at the wall, padding rescuing reclaim, sf failing) | — |

The **cross-check outcome is a separate protocol-fidelity line** (AGREE / DISCREPANT +
audit finding), reported beside the claim verdicts. It cannot flip a claim verdict —
those are judged-once records of what *our* protocol measured — but a DISCREPANT
cross-check goes into the README headline sentence verbatim, not into a footnote.

**Bootstrap decides nothing (D4, restated).** Wilson/Newcombe decided every gate and
still do. The appendix prints both methods side by side for every gated cell and gap;
any disagreement is flagged and Wilson stands; the expected 0/n degeneracy is named
above, in advance.

**The checkpoint (the oracle run's analog of N=20, $0):** the run stages through their
own documented smoke-then-resume pattern. After `--seeds 1` (96 units, ~1,632 calls):
recount every cell from their checkpoint rows with `m3.py` and confirm the recount
matches their console table; spot-check ≥3 rows per policy for internal consistency
(their logged answer vs their correct flag vs the fixed problem's known truth and drift
values); confirm measured per-unit cost against the estimate. Only then `--seeds 3`
(resume pays only the remaining 192 units). Nothing is judged at seed 1; the checkpoint's
powers are bug-catching and cost-confirmation only, exactly as at every previous
milestone.

## Decisions — pick or veto (recommendation marked; numbering continues DECISIONS.md)

### D19 · The oracle run: their pilot, their defaults, the paper economy, on llama

- **A. Their `run_pilot.py --real --fix --task arith` on llama at tool defaults
  (temperature 0.0, all 32 problems) × 3 seeds → n=96/cell (Recommended).** ~4,896 calls
  ≈ $0.08–0.15 with headroom, staged seed-1-then-resume. *Merit:* reproduces the paper's
  own tab:wall economy cell-for-cell (their-run vs paper-committed is n-matched, so any
  gap there is drift or provider, not power); sampling-matched to our archived cells by
  construction (their tool default = our D10); the agreement criterion has real teeth at
  n=96 (boundary table above). *Trade-off:* their runner is strictly serial and we don't
  touch their code — ~2.5–4.5 h wall-clock in the background (resume-safe), the longest
  single run of the project.
- **B. The README cost-note economy: `--n 8` × 3 seeds → n=24/cell.** ~1,224 calls ≈
  $0.02–0.04, ~45–75 min. *Merit:* cheapest and fastest; matches their README's "8
  problems × 3 seeds = 1224 calls" arithmetic (which predates their problem-set growing
  to 32 — their tool's default now runs all 32). *Trade-off:* 0/24 vs our 0/40 spans [−8.8%, +13.8%] — the same criterion with
  roughly double the blind spot, and their-run vs paper-committed is no longer n-matched.
  Saves ~$0.10 on a project whose binding constraint has never been cost.
- **C. deepseek as the overlap model.** *Merit:* would probe their parser blindspot on
  live data. *Trade-off:* it points the one protocol-validation instrument at a cell
  where THEIR readout is known-suspect — a disagreement couldn't tell our-protocol-drift
  from their-parser-bug, which is the confound the cell exists to avoid. The blindspot is
  already proven for free by the fixture check; llama is the paper's primary model and
  D3's named anchor.

**Rider (a) — repeat the run at temperature 0.7? (recommended: no).** Their README's
original core sweep says 0.7; the paper-extraction task will pin what the paper states
for tab:wall. A 0.7 repeat (~+$0.10, +hours) would buy a sampling-sensitivity read, but
it adds a second oracle number for the same cells (two numbers for one condition — the
ambiguity judged-once exists to prevent), and the comparison's job is direction and
structure, not point-matching (KICKOFF's non-goal). If the paper turns out to state 0.7
for tab:wall, the table's temperature column carries that label and the caveat — which is
the honest treatment either way.

*Why A:* it is the author's own protocol at the author's own published cell size, run
through the author's own code with nothing modified — the strongest form of the D1
promise — for about a dime and one long background run.

### D20 · What the cross-check can change: a protocol-fidelity line, not a re-judging

- **A. Per-claim verdicts stand as judged; the cross-check adds a separate
  protocol-fidelity line; the mapping table above is committed before the run
  (Recommended).** *Merit:* judged-once stays intact (the claim verdicts describe our
  measurements, which the oracle run does not re-measure); a discrepancy still lands in
  the README headline sentence with its audit finding — visible, not buried; the mapping
  can't be tuned after the data exists. *Trade-off:* a reader must hold two things (claim
  verdicts + fidelity line) instead of one compound verdict.
- **B. The cross-check gates the headline: REPRODUCED requires AGREE.** *Merit:* maximal
  teeth, one-word verdict. *Trade-off:* it hands the author's harness a veto over our
  verdict — and their artifact has two already-documented defects (the broken replay, the
  parser blindspot), so a DISAGREE could indict their code rather than our protocol;
  compounding them into one word is exactly the ambiguity the audit exists to separate.
- **C. No pre-committed mapping; write the README after seeing everything.** *Merit:*
  none worth having. *Trade-off:* the researcher degree of freedom this project has spent
  three milestones closing off, reopened at the finish line.

**Rider (a) — the pre-declared descriptive recount (recommended: yes).** Count the
wrong-emission split of the **archived** llama and qwen72b lossy@0.1 rows (n=40 each,
$0, counted once at table time, gating nothing) so their tab:blank lossy-emit values
(llama 0.17) get a same-protocol neighbor in the table. This extends nothing D17
declined: the blank arms stay at probe n=12, no new trials run, no gap is gated — it is a
declared-in-advance descriptive count of rows that already exist, the D18 pattern.

*Why A:* the claim verdicts and the protocol-fidelity question are different measurements
of different things; keeping them separate is what makes both reportable honestly.

### D21 · bootstrap.py: their method verbatim, over every gated cell and gap

- **A. Percentile bootstrap, B=5,000, seed 0 — their `boot_ci` re-typed — for every
  GATED cell rate and gap in claims 1–3; appendix table beside Wilson/Newcombe; Wilson
  decides (Recommended).** *Merit:* discharges D4's promised appendix with the author's
  exact method (no "which bootstrap?" ambiguity); covers precisely the numbers that
  decided verdicts; the 0/n degeneracy becomes a shown, taught result instead of a
  surprise. *Trade-off:* ~40 appendix rows nobody gates on.
- **B. Claim-1 cells only.** *Merit:* the smallest discharge of the promise.
  *Trade-off:* claims 2 and 3 were gated on the same interval machinery; a robustness
  appendix that skips two of three claims invites "why only there?"
- **C. Every cell including the knob descriptives.** *Merit:* completeness.
  *Trade-off:* the knob cells gate nothing and already wear Wilson bars on the committed
  figures; bootstrap columns there are decoration.

*Why A:* the appendix's job is to let a reader check that the method choice never drove a
verdict — so it must cover exactly the verdict-driving numbers, and nothing else needs
it.

### D22 · The capstone: one composite figure

- **A. One `docs/figs/capstone.png`: knob curves per model + claim-3 emission bars + the
  cross-check comparison panel (Recommended).** *Merit:* a single self-contained image
  that carries the whole v1 story (the wall, the control, the title claim, and the
  independent-build check) — the artifact that travels in a README, a post, or a
  portfolio; built entirely from archived rows + the oracle run, $0. *Trade-off:* one
  more figure to build; the milestone figures stay frozen so there is some redundancy.
- **B. Bless `m2-knob.png` + `m2-emission.png` as the capstone pair.** *Merit:* zero new
  code. *Trade-off:* no single shareable image; the cross-check — M3's whole point —
  never gets visualized.
- **C. A without the cross-check panel (comparison stays a table).** *Merit:* simpler
  figure. *Trade-off:* same blind spot as B on the one new M3 result.

*Why A:* v1's deliverable is "one legible artifact"; a capstone that needs three files
and a paragraph of arrangement isn't one.

## M3 task list, free-before-paid, exit criteria

Order matters: **nothing paid runs until every free check is green**, and the agreement
judge is committed in code before the oracle run produces its first row.

1. **Sign-off** on D19–D22 (this brief).
2. **Build `bootstrap.py` + `test_bootstrap.py`, TDD, $0:** their `boot_ci` re-typed with
   attribution (percentile, B=5,000, seed 0); independent two-arm resampling for gaps;
   the 0/n degeneracy pinned by a test; appendix-table subcommand over the archived
   evidence.
3. **Build `m3.py` + `test_m3.py`, TDD, $0:** their `fix_*.jsonl` reader; the agreement
   judge as a pure function with the boundary arithmetic above pinned by tests; the D20
   rider-a recount; the comparison-table builder; the capstone figure subcommand. Full
   pytest + anti-rig suite green before any paid call.
4. **Free oracle-side checks, $0:** the fixture check on their `parse_answer` (script in
   their clone, their venv, output to `evidence/m3/`); re-run their DryRun probe and
   `reproduce_tables.py` to reconfirm the M0 findings on the current clone; the
   paper-number extraction (tab:wall llama row + CI brackets, disposition/blank rows,
   stated sampling config) with citations.
5. **The oracle run, staged (the only paid item):** our key into their `.env` (never
   committed); their probe first (1 call, slug + per-call cost); `--seeds 1` → **the M3
   checkpoint** (recount vs their console table; ≥3-row consistency spot-check per
   policy; per-unit cost vs estimate) → `--seeds 3` resume to n=96/cell. Console logs
   captured.
6. **Judge the cross-check** ($0, the pure function over their rows + our archived
   comparators); AGREE/DISCREPANT recorded with all six intervals; on DISCREPANT, the
   pre-committed audit runs and its finding is written up either way.
7. **Assemble the comparison table** into `ROADMAP.md` (and the README's short form),
   every column labeled (method / n / temperature / problem economy / arm), the two
   protocol findings and the fixture result as its footnotes.
8. **Capstone figure committed** (`docs/figs/capstone.png`); **README story rewritten**
   around the verdict mapping (D20's table applied mechanically); milestone figures
   untouched.
9. **Evidence + ledger + spine close-out, same PR:** their checkpoint JSONL + console
   logs + fixture output copied to `evidence/m3/` (key-scan clean, D15); measured M3 cost
   appended to `ROADMAP.md`; D19–D22 outcomes into `DECISIONS.md`; `LEARNING.md` M3
   teaching note + new words + 3 recall questions; README status; ROADMAP M3 section.
   The close-out also hands Kyle the one post-v1 decision this brief does *not* make:
   whether the gated M4 (logic family) / M5 (boundary arm) open — the effect showed, so
   KICKOFF's gate condition is met — or v1 closes here and `/seed-hunt` runs. That is a
   fresh decision brief at close, not a task.

**Exit criteria:** a cross-check verdict recorded with all six cells' intervals, judged
only by the pre-committed criterion; the comparison table committed with every column
labeled and both protocol findings footnoted; `bootstrap.py` green with the appendix
table committed and any Wilson-vs-bootstrap disagreement flagged; the capstone figure
committed; the README story rewritten under the pre-committed mapping; the M3 checkpoint
documented; evidence committed per D15; measured M3 cost in the ledger; all spine updates
in the closing PR.

## Cost and wall-clock (from ROADMAP's measured M1/M2 numbers)

llama's measured session-scale cost: ~$0.010 per 59-trajectory bank ≈ $0.000017/call.
Their unit is 17 calls (9 session-1 + 8 short session-2). Estimates carry the usual
1.5–2× headroom.

| item | calls (approx) | estimate |
|---|---|---|
| oracle probe (1 call, slug + cost) | 1 | <$0.001 |
| oracle run, paper economy (D19-A): 288 units × 17 | 4,896 | ~$0.08–0.15 |
| — of which the seed-1 smoke stage | 1,632 | ~$0.03–0.05 |
| bootstrap.py, m3.py, fixture check, extraction, table, capstone, README, spine | 0 | $0 |
| **base M3 (D19-A + D20-A + D21-A + D22-A)** | ~4.9k | **≈ $0.10–0.15** |
| contingency: discrepancy audit (code/note diffing, hand recount) | 0 | $0 |
| contingency: one bounded targeted re-run if the audit demands it (≤1 seed) | ≤1,632 | ≤$0.05 |
| rider D19(a) if yes: temperature-0.7 repeat | +4,896 | +$0.08–0.15 |
| D19-B instead: README pilot economy (n=24/cell) | 1,224 | ~$0.02–0.04 |

Hard ceiling with every contingency and the rider: ≈ $0.35. Running project total after
M3: ≈ **$1.0–1.1** of KICKOFF's "likely under $10." The binding constraint remains
statistics — and in M3, mostly wall-clock.

Wall-clock: their runner is serial and stays unmodified — seed-1 smoke ≈ 45–90 min,
full run ≈ 2.5–4.5 h, both unattended in the background and resume-safe (their per-unit
checkpointing; a crash or throttle loses at most one unit). The checkpoint recount and
consistency read is ~20–30 min of human time; the free builds and the write-up are the
usual evening. One evening plus one long background hum, plus this sign-off.

## Explicitly NOT in M3

- Any new cell on our harness, any re-run of any judged cell (D14), any bank
  regeneration, any roster change, any re-litigation of M0–M2 verdicts or of D7's δ.
- M4 (logic family) and M5 (boundary arm) — gated post-v1 (D2); the close-out *presents*
  that gate decision to Kyle, it does not make it.
- Importing the author's package anywhere in our code, or adding it to `pyproject.toml`
  (D1's wall — their code runs only in their clone, under their venv).
- Gating anything on their generic-arm rows (our paid cells are directed-only, D2);
  point-estimate matching of any kind (KICKOFF non-goal: direction + structure only).
- Any new readout: their rows arrive scored by their code; ours stay scored by the
  M0-era parser + classifier. The `\$` widening (PR #10) never reverts.

## New words introduced here

- **Oracle run** — the one paid execution of the author's own harness, used as an
  external reference to check our independent build against; "oracle" because we treat
  its protocol as the ground truth to compare with, not because it is infallible (its two
  known defects are part of the report).
- **Replication vs re-run** — running the author's code again tests their code;
  rebuilding from the paper and comparing on one cell tests whether the *description* of
  the method is complete. D1 chose the second; the oracle run is the comparison point.
- **Paper economy** — the paper's own cell size and trial bookkeeping (here 32 fixed
  problems × 3 seeds = n=96/cell, session 1 rebuilt per policy), as opposed to our D5
  economy (fresh problem per trial, one trajectory shared across policies).
- **Bootstrap (percentile)** — an interval built by resampling: redraw the observed
  trials with replacement B times, recompute the rate each time, and read the 2.5th and
  97.5th percentiles of those B rates as the interval. Distribution-free, but degenerate
  at extreme cells (see next).
- **Degenerate interval** — an interval that collapses to a point because the resampling
  can't produce variation (every redraw of 0/40 is 0/40 → [0.000, 0.000]); false
  certainty exactly where the data are most extreme, and the reason Wilson decides gates.
- **Agreement / consistency criterion** — the pre-committed rule for "same result from
  two builds": the Newcombe interval on (their rate − ours) contains zero on every gated
  overlap cell. Chosen before the data exists, like every other gate in this project.
- **Protocol audit** — the pre-committed response to a DISCREPANT cell: diff the protocol
  artifacts (note strings, frame, correction wording) before suspecting the readout, and
  report whatever is found, including "unexplained."
- **Verdict vocabulary** — the four pre-committed words a replication is allowed to end
  on (REPRODUCED / PARTIAL / NULL / DISCREPANT), with mechanical rules for each, fixed
  before the last measurement so the ending can't be written to fit.
