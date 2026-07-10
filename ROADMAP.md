# ROADMAP.md — milestone status

Scope source of truth: `docs/KICKOFF.md` (phased plan + gate record). Decisions live in
`DECISIONS.md`; teaching notes in `LEARNING.md`; per-stage briefs in `docs/`.

| Milestone | What it is | Status |
|---|---|---|
| **M0 — the fit-pilot** | de-risk: machinery + drift-take pilot + disposition probe | **complete (2026-07-06)** |
| M1 — the wall | lossy vs source_first @ g=0.1/0.3, claim 1, wall figure | **complete (2026-07-06)** — claim 1 CLEARED, 3/3 models |
| M2 — the controls | lossy_padded (claim 2) + blank/emission (claim 3), knob fills | **complete (2026-07-07)** — claim 2 CLEARED 3/3, claim 3 CLEARED (deepseek) |
| M3 — cross-check + capstone | author's harness on the overlap cell, comparison table, capstone | **complete (2026-07-08)** — cross-check **AGREE** (6/6 intervals) |
| **M4 — logic family** | soft wall / task-generality; gap-gated + taxonomy, N=60 | **complete (2026-07-08)** — **PARTIAL**; deepseek clears both claims, qwen confounded (ordering × directed correction) |
| **M5 — boundary arm** | source-size cliff: where source_first fails, the paper's design | **complete (2026-07-09)** — **REPRODUCED**; crossover tracks the budget (N=4@300, N=12@600) |

**PROJECT CLOSED 2026-07-09 (D31).** KICKOFF's phased plan is exhausted — v1 claims 1–3
REPRODUCED + cross-check AGREE, and both gated post-v1 arms judged (M4 PARTIAL, M5 REPRODUCED).
Total measured spend ≈ $2.13. Next move: `/seed-hunt`.

---

## M0 — the fit-pilot · complete 2026-07-06

Free half (PRs #1–#5): ported client/stats/ping; problems generator, four note
policies, ANSWER-line grader; two-session runner with the per-trial source gate;
anti-rig validator suite 3/3 green on the deterministic fake; author's harness
installed as an isolated $0 oracle (their DryRun agrees with our fake; their
`reproduce_tables.py` exits 1 on the public repo — empty `data/results/` — recorded as
a replication finding for M3).

Paid half (this PR): `m0.py` pilot driver; ping; drift-take pilot; disposition probe;
two live scoring fixes (D11); one roster swap (D8 fired path). All verdicts below were
pre-committed in `docs/M0-BRIEF.md`/`DECISIONS.md` before any data existed.

### D8 — drift-take verdicts (N=20/model, depth 8, temperature 0.0)

| model | take | rate | Wilson 95% | verdict |
|---|---|---|---|---|
| llama-3.1-8b-instruct | 14/20 | 70% | [48%, 85%] | **GREEN** — proceed as planned |
| deepseek-chat | 13/20 † | 65% † | [43%, 82%] † | **AMBER** † — proceed; session-1 generation inflated ~1/0.65 ≈ 1.5×; weak take noted in README |
| qwen-2.5-7b-instruct | 5/20 | 25% | [11%, 47%] | **TRIGGER** — fired; see swap below |
| qwen-2.5-72b-instruct (swap) | 3/4 | — | — | **attempt infrastructure-blocked** — verdict deferred to the M1 brief |

qwen-7b's fired path ran as pre-committed: fidelity audit (plant/follow-ups/system
prompt verbatim-confirmed against the author's `experiment.py`; llama and deepseek
drift fine on the same problems — the resistance is the model's disposition: it
re-derives the correct total), then a same-family swap (Kyle): qwen-2.5-14b-instruct
was the pick, OpenRouter no longer lists it (ping caught it), so the sub is
qwen-2.5-72b-instruct — the only other 2.5-instruct sibling — route-pinned to
DeepInfra (the Novita fallback hard-400s chat completions). The pinned route then
couldn't carry a 210-call arm: DeepInfra's upstream throttle outlasted 8 backoff
retries, twice. The 4 completed trials took 3/4 — promising — so the 72b re-attempt
is deferred to the M1 brief (when the route recovers, or with a direct provider key),
and **M0 closes two-model (llama + deepseek), exactly as D8's fired path allows.**

### D9 — disposition probe verdicts (lossy vs blank @ g=0.1, 12/arm, directed)

| model | wrong lossy | wrong blank | gap | Newcombe 95% | verdict |
|---|---|---|---|---|---|
| llama | 1/12 | 0/12 | +1 | [−17%, +35%] | **NULL** on this model — the paper's predicted abstainer behavior (11/12 lossy abstains, 12/12 blank) |
| deepseek | 10/12 † | 0/12 | +10 † | [+46%, +95%] † | **GREEN** — claim 3 measurable at M2's N≈40 |
| qwen-7b | — | — | — | — | skipped: D8 trigger fired (probe runs on survivors only) |
| qwen-72b | — | — | — | — | deferred with its pilot (M1 brief) |

The headline: deepseek reproduces the title claim's shape at full strength — holding a
lossy note at the wall it confidently emits wrong values (6 attractor re-emissions + 4
other-wrong of 12), while with a blank memory it abstains 12/12. Both riskiest
assumptions (drift takes; the gap is powerable at hobby N) are answered YES.

### † Correction (2026-07-06, found during M1): the escaped-dollar parser blindspot

M1's mandatory bank hand-read caught it live: deepseek LaTeX-escapes the currency
symbol on roughly a third of its ANSWER lines (`ANSWER: \$197`), and `parse_answer` —
re-typed verbatim from the author's `llm.py` — read those as "no numeric commit."
Every such reply in M0's archived evidence committed a real value. Rescoring
`evidence/m0/` with the widened parser (the `\$` escape accepted only immediately
before the value — refusal prose still parses to None, so the paper's v2 bug can't
return through this door):

- **deepseek drift-take: 20/20, GREEN** (Wilson [84%, 100%]) — all seven scored
  "no-takes" were escaped drift commits. The AMBER tier and its ×1.54 generation
  mandate were parser artifacts; the mandate is lifted (M1's bank builder runs to a
  take target, so nothing downstream depends on t̂).
- **deepseek disposition probe: lossy 11/12 vs blank 0/12** — gap +11, Newcombe
  [+55%, +99%]. The GREEN verdict stands, stronger.
- **llama, qwen-7b, qwen-72b: unchanged everywhere** (zero escaped replies).

Every error ran conservative — true takes discarded, a wrong emission read as an
abstention — so no M0 verdict flipped against the claims; the two GREENs got greener.
The evidence files remain byte-verbatim; this note is the correction of record.
A protocol note for M3's comparison table: the author's parser carries the same wrap
set, so their deepseek cells may under-read the same way — worth checking at the
cross-check cell.

### Cost ledger (OpenRouter-measured via usage.include, except where noted)

| item | cost |
|---|---|
| ping (3 models) | $0.000006 |
| pilot pass A (killed early — cents-bug discovery; ~11 partial trials) | ~$0.01 (estimate; killed before summary) |
| pilot pass B (full 3×20 under the pre-D11 readout; trajectories valid, verdicts discarded) | $0.065357 |
| pilot pass C (D11 readout: llama + deepseek + qwen-7b) | $0.069694 |
| disposition probes (llama + deepseek) | $0.002847 |
| qwen-72b diagnostics (route probing, ~10 micro-calls) | <$0.001 |
| qwen-72b pilot attempts (2, infrastructure-blocked; 4 measured trials) | $0.0105 + ~$0.005 est |
| **M0 total** | **≈ $0.165** (~$0.149 measured + ~$0.016 estimated on killed partials) |

Extrapolation to full v1 (M1+M2 grids at N=40 with D5 pairing — one session-1
trajectory serves all four policy notes per trial — plus take-rate inflation, plus the
M3 cross-check cell): roughly **$2–4**, comfortably inside KICKOFF's "likely under
$10." The M1 brief re-does this arithmetic against measured per-model costs.

### Exit criteria checklist

- [x] anti-rig 3/3 + full pytest green before the first paid call (60 tests at ping
      time; 64 by close)
- [x] a D8 verdict and a D9 verdict recorded per model (table above)
- [x] measured cost ledger written (above)
- [x] spine updates in the same PR as the closing code (this PR: ROADMAP.md,
      DECISIONS.md D10–D11, LEARNING.md M0, README status)

---

## M1 — the wall · complete 2026-07-06

Brief signed same day (PR #7; D13–D15 recorded, PR #8). Harness: `m1.py` +
`test_m1.py` (PR #9) — bank / grid / checkpoint / judge / figure, with the D14
ladder pre-committed as pure functions. One live scoring fix mid-milestone: the
escaped-dollar parser blindspot (PR #10; the † correction above). All verdicts below
were judged only by the pre-committed D14 ladder.

### D13 — the third-model slot, resolved

The bounded re-attempt completed cleanly: **18/20 takes, D8 GREEN** (Wilson
[70%, 97%], $0.056). D9 probe: **claim-3 NULL** — 0/12 wrong emissions on both arms,
every reply an abstention (72b is an abstainer at the wall, like llama; deepseek
remains the roster's only emitter — an M2 fact, not an M1 blocker). **Roster frozen
at three:** llama + deepseek + qwen-2.5-72b-instruct, the 72b labeled in every table
as a same-family, 10×-size substitution for the paper's qwen-2.5-7b, never as the
paper's model.

### The trajectory banks (fresh `m1-` schedule, shared across models; D5/D11)

| model | taken / raw trials | post-fix take rate |
|---|---|---|
| llama | 40/59 | 0.68 |
| deepseek | 90/98 (escalation top-up included) | 0.92 |
| qwen72b | 40/44 | 0.91 |

Banks are committed under `evidence/m1/` (D15) — they are M2's input: the g=1.0
lossy cell carries the full session-1 transcript, and every trajectory is logged.

### The checkpoint (N=20 interim look, D14)

No futile cell. 36 sampled trials + the one stray reclaim hand-read and verified —
record in `evidence/m1/m1-checkpoint/RECORD.md`. The hand-read caught the
escaped-dollar parser bug before any cell scaled past 20 (the † correction above) —
the M0 lesson (validators prove mechanics, eyes prove readouts) paying for itself.
source_first, never run in M0, read 20/20 everywhere with hand-verified
recomputation — no protocol-fidelity concern against the paper's 0.99–1.00.

### D14 — claim-1 verdicts (ceiling 0.10 on the lossy Wilson-95 upper bound; Newcombe gap > 0; both g)

| model | lossy@0.1 | lossy@0.3 | sf@0.1 | sf@0.3 | gap@0.1 (Newcombe) | gap@0.3 (Newcombe) | verdict |
|---|---|---|---|---|---|---|---|
| llama | 0/40 [0%, 8.8%] ✓ | 0/40 [0%, 8.8%] ✓ | 40/40 [91%, 100%] | 40/40 [91%, 100%] | +100% [+87.6%, +100%] | +100% [+87.6%, +100%] | **CLEARED** |
| deepseek | 1/90 [0.2%, 6.0%] ✓ (escalated) | 0/40 [0%, 8.8%] ✓ | 40/40 [91%, 100%] | 40/40 [91%, 100%] | +99% [+88.8%, +99.8%] | +100% [+87.6%, +100%] | **CLEARED** |
| qwen72b | 0/40 [0%, 8.8%] ✓ | 0/40 [0%, 8.8%] ✓ | 40/40 [91%, 100%] | 40/40 [91%, 100%] | +100% [+87.6%, +100%] | +100% [+87.6%, +100%] | **CLEARED** |

**v1 claim 1: CLEARED — 3 of 3 models** (bar was ≥2). The sf replicate check
(sf@0.1 vs sf@0.3, identical note strings by the g-threshold mapping) is consistent
on every model (+0%, [−8.8%, +8.8%]).

The one escalation ran exactly as pre-committed: deepseek's lossy@0.1 stray at N=40
(1/40 → upper bound 12.9%) was hand-read (a lucky round-number confabulation with no
source in context — the paper's DryRun "lucky recovery" case, kept as a reclaim under
strict scoring), the cell extended once to N=90, gained zero reclaims in 50 further
trials, and cleared at [0.2%, 6.0%]. The cleared lossy@0.3 cell was not re-touched
(judged once).

The wall figure: `docs/figs/m1-wall.png` — RR vs g per model, Wilson bars, x-axis
laid out for the full knob so M2's g=0.6/1.0 and lossy_padded/blank cells drop in.

### Cost ledger (OpenRouter-measured via usage.include, except where noted)

| item | cost |
|---|---|
| D13: 72b pilot re-attempt (20 trials) + D9 probe | $0.056 + $0.002 |
| llama bank (59 trials) | $0.010 |
| deepseek bank (98 trials: ~23 pre-kill est. + 20 + 55 measured) | ~$0.050 est + $0.157 |
| qwen72b bank (44 trials: ~14 pre-throttle est. + 30 measured) | ~$0.040 est + $0.085 |
| grids: llama 20+40 · deepseek 20+40+escalation · 72b 20+40 | $0.002 + $0.031 + $0.020 |
| **M1 total** | **≈ $0.45** (~$0.36 measured + ~$0.09 estimated on killed partials) |

Inside the brief's envelope (base $0.20–0.30 two-model; ceiling ≈$1.2 with the third
model and every escalation — one escalation fired). Running project total ≈ $0.62.

### Exit criteria checklist

- [x] a claim-1 verdict per model per wall g, both components' intervals recorded,
      judged only by the pre-committed ladder (table above)
- [x] the checkpoint hand-read documented (`evidence/m1/m1-checkpoint/RECORD.md`)
- [x] the wall figure committed (`docs/figs/m1-wall.png`)
- [x] evidence committed per D15 (`evidence/m1/`, 233 files, ~1.8 MB, key-scan clean)
- [x] measured M1 cost in the ledger (above)
- [x] spine updates in the same PR as the closing code (this PR: ROADMAP.md,
      LEARNING.md M1, README status; D13's outcome landed in DECISIONS.md at PR #8)

## M2 — the controls · complete 2026-07-07

Brief signed same day (PR #12; D16–D18 recorded). Harness: `m2.py` + `test_m2.py`
(PR #13) — grid / checkpoint / judge / figures over M1's banks, with D16's
containment ladder, the claim compositions, and D17's blind-committed counting rule
pre-committed as pure functions (29 tests; the judge mechanically refuses to tally
claim 3 before the blank cell's final N). Zero M1 cells re-run (judged once); every
M2 cell is a write-time transformation of the same bank trajectories (D5 pairing).

### The checkpoint (N=20 interim look; no futility screen — D16)

All seven new cell shapes hand-read per the brief's M2-specific eyes; record in
`evidence/m2/m2-checkpoint/RECORD.md`. Padded notes verified mechanically on EVERY
row (filler present, source absent, length ≥ the sf note); transcript cells carry
the genuine 19-turn drift conversations; deepseek's blank replies read as a human
would (explicit declines, no parsed value). Both stray padded reclaims were read
individually — both are the lucky-recovery case (a model assuming a value with no
source in context and landing on truth), kept under strict scoring; the ladder did
its job on both. llama's knob dip got the +1 targeted read: token-cap abstains plus
genuine attractor re-emissions, correctly scored — real behaviour, not a readout bug.

### D16 — claim-2 verdicts (equivalence: Newcombe on padded − lossy inside ±0.10; separation: sf − padded excludes zero; both g)

| model | padded@0.1 | padded@0.3 | equivalence @0.1 | equivalence @0.3 | separation @0.1 | separation @0.3 | verdict |
|---|---|---|---|---|---|---|---|
| llama | 0/40 | 0/40 | +0% [−8.8%, +8.8%] ✓ | +0% [−8.8%, +8.8%] ✓ | +100% [+87.6%, +100%] | +100% [+87.6%, +100%] | **CLEARED** |
| deepseek | 1/90 (escalated) | 0/40 | +0% [−5.0%, +5.0%] ✓ | +0% [−8.8%, +8.8%] ✓ | +99% [+88.8%, +99.8%] | +100% [+87.6%, +100%] | **CLEARED** |
| qwen72b | 0/40 | 1/90 (escalated) | +0% [−8.8%, +8.8%] ✓ | +1% [−7.7%, +6.0%] ✓ | +100% [+87.6%, +100%] | +99% [+88.8%, +99.8%] | **CLEARED** |

**v1 claim 2: CLEARED — 3 of 3 models** (bar was ≥2). Same character budget, same
lossy content plus content-free filler: padding rescued nothing (every padded cell
statistically indistinguishable from plain lossy inside the pre-committed ±10%),
while source_first beats the padded note by ≥ +87.6% everywhere — the correction
runs on what the characters SAY, not how many there are.

Both escalations ran exactly as pre-committed, and both landed on boundary cases the
brief had computed in advance: deepseek's padded@0.1 stray (1/40 vs its archived
1/90 lossy comparator → +11.8%, escalate) gained zero reclaims in 50 more trials and
contained at ±5.0%; qwen72b's padded@0.3 stray (1/40 vs 0/40 → +12.9%, escalate)
first triggered the priced bank top-up (40 → 90 taken, 62 trials, no throttle
death), then likewise gained zero and contained at [−7.7%, +6.0%]. The contained
sibling cells were never re-touched (judged once).

### D17 — claim-3 verdict (wrong-emission gap, lossy − blank, excludes zero; deepseek)

| arm | wrong | attractor | other-wrong | abstain | reclaimed |
|---|---|---|---|---|---|
| lossy@0.1 (M1 archived, n=90) | **52/90** (58%) | 33 | 19 | 37 | 1 |
| blank (new, n=40) | **0/40** (0%) | 0 | 0 | 40 | 0 |

Gap **+58%, Newcombe [+44.2%, +67.5%] — CLEARED.** The counting rule was committed
blind on 2026-07-07 (the archived split untallied until judge time, enforced in
code); the honest caveat stands as pre-registered: the two arms were sampled on
different dates (temperature 0.0, same pinned models/routes, same bank
trajectories). Holding a blank memory, deepseek declined 40/40 times; holding a
lossy note over the identical trajectories, it confidently emitted a wrong figure
58% of the time — the lossy note is worse than nothing. The abstainers keep their
probe NULLs, reported plainly per KICKOFF (llama +1/12, qwen72b 0/12; D17 rider a:
not extended).

### D18 — the knob fills (descriptive, N=40 uniform, gate nothing)

deepseek and qwen72b sit at the reclaim ceiling in all four knob cells (40/40:
lossy@0.6, lossy@1.0-transcript, sf@0.6, sf@1.0) — above the source threshold the
two policies converge, as the protocol predicts. llama shows a real dip at high g
(lossy@0.6 38/40; lossy@1.0 28/40; sf@0.6 27/40; sf@1.0 26/40; replicate check
consistent at −3% [−22.4%, +17.6%]): the checkpoint's targeted read attributes it
to llama rambling into its 600-token cap without an ANSWER line (abstains under the
strict readout, several with the correct total computed mid-reply) plus genuine
attractor re-emissions with the source in hand. Both figures committed:
`docs/figs/m2-knob.png` (full curves, padded points at the wall, blank's reclaim
point on the deepseek panel) and `docs/figs/m2-emission.png` (claim 3's picture).
`m1-wall.png` untouched (M1's committed record).

### Cost ledger (OpenRouter-measured via usage.include, from the logged rows)

| item | cost |
|---|---|
| llama grid (240 rows) | $0.004 |
| deepseek grid (330 rows, escalation included) | $0.061 |
| qwen72b grid (290 rows, escalation included; one 429 crash, resumed) | $0.053 |
| qwen72b bank top-up 40 → 90 taken (62 trials, D16 contingency) | $0.174 |
| **M2 total** | **$0.293 measured** |

Inside the brief's base envelope ($0.25–0.35) even with both escalations and the
full top-up contingency firing (hard ceiling was ≈$0.75). Running project total
≈ **$0.91** of KICKOFF's "likely under $10"; M3's cross-check cell remains.

### Exit criteria checklist

- [x] a claim-2 verdict per model per wall g, both components' intervals recorded,
      judged only by the pre-committed ladder and composition (table above)
- [x] a claim-3 verdict on deepseek with both arms' splits + abstainer nulls
      restated plainly (table above)
- [x] the checkpoint hand-read documented (`evidence/m2/m2-checkpoint/RECORD.md`)
- [x] both figures committed (`docs/figs/m2-knob.png`, `docs/figs/m2-emission.png`)
- [x] evidence committed per D15 (`evidence/m2/`, 71 files, ~1.5 MB, key-scan clean)
- [x] measured M2 cost in the ledger (above)
- [x] spine updates in the same PR as the close-out (this PR: ROADMAP.md,
      DECISIONS.md D16–D18 outcomes, LEARNING.md M2, README status)

## M3 — cross-check + capstone · complete 2026-07-08

Brief signed 2026-07-07 (PRs #15/#16; D19–D22 recorded). Free builds: `bootstrap.py`
(PR #17, D21's appendix) and `m3.py` (PR #18, the judge/table/capstone machinery), both
TDD with the agreement boundary arithmetic pinned at the brief's published values before
any data existed. Free oracle-side checks (PR #19): the parser fixture, both M0-finding
reconfirmations, their problems dumped as data, and the arXiv v2 extraction
(`evidence/m3/paper-extraction.md`).

### The oracle run (D19-A — their code, their defaults, the paper economy)

`run_pilot.py --real --fix --task arith` on llama-3.1-8b-instruct from their clone,
their venv, nothing modified: 32 problems × 3 seeds × 3 policies = 288 units × 17 calls
= **4,896 calls, n=96 per (policy, g, arm) cell**, temperature 0.0 (their tool default =
our D10 — sampling-matched to our archived cells by construction). Staged exactly as
pre-committed: seed-1 smoke (96 units, $0.018, 12,390s) → **the M3 checkpoint** →
`--seeds 3` resume (192 units, $0.037, 14,782s). Wall-clock ~7.6h serial on a slow
provider day (measured pace 120–200s/unit vs the brief's 28–56s estimate; cost
unaffected — the estimate's error was wall-clock only).

**The checkpoint record (powers: recount + eyes + cost, nothing judged):** our recount
of their checkpoint rows matched their console table **cell-for-cell at 2 decimals,
both arms** (`evidence/m3/m3-checkpoint-recount-seed1.txt`); the spot-check read 9
sampled rows (3 per policy) against the problems' known truth/drift — **9/9 internally
consistent**, including one sampled generic-arm padded row that emitted the planted
drift value and was correctly flagged wrong by their scorer; per-unit cost $0.0002
(under the estimate).

### The cross-check verdict (D20's pre-committed criterion)

Newcombe 95% on (their rate − our archived rate), all six gated overlap cells
(`evidence/m3/m3-agreement-judge.txt`):

| cell | theirs (n=96) | ours (archived) | d [95% CI] | reading |
|---|---|---|---|---|
| lossy@0.1 | 0/96 | 0/40 | +0.000 [−0.088, +0.038] | consistent |
| lossy@0.3 | 1/96 | 0/40 | +0.010 [−0.078, +0.057] | consistent |
| lossy_padded@0.1 | 0/96 | 0/40 | +0.000 [−0.088, +0.038] | consistent |
| lossy_padded@0.3 | 0/96 | 0/40 | +0.000 [−0.088, +0.038] | consistent |
| source_first@0.1 | 96/96 | 40/40 | +0.000 [−0.038, +0.088] | consistent |
| source_first@0.3 | 96/96 | 40/40 | +0.000 [−0.038, +0.088] | consistent |

**Verdict: AGREE — all six intervals contain zero.** No audit fires. Their one stray
(lossy@0.3, 1/96) is the same lucky-recovery class our deepseek escalation documented
in M1. Their internal wall structure, descriptive: sf−lossy +100% [+94.6%, +100%] at
g=0.1, +99% [+92.9%, +99.8%] at g=0.3 — the paper's structure through their own
harness, beside ours through ours.

### The comparison table (D20 — full form; README carries the short form)


| cell | tier | paper-committed | their-harness-run | ours |
|---|---|---|---|---|
| lossy@1 | descriptive | 0.61 B[0.52, 0.71] (n=96) | 62/96 = 0.65 W[0.55, 0.73] B[0.54, 0.74] | 28/40 = 0.70 W[0.55, 0.82] |
| lossy_padded@1 | descriptive | 0.85 B[0.78, 0.92] (n=96) | 86/96 = 0.90 W[0.82, 0.94] B[0.83, 0.96] | — |
| source_first@1 | descriptive | 0.61 B[0.52, 0.71] (n=96) | 61/96 = 0.64 W[0.54, 0.72] B[0.54, 0.73] | 26/40 = 0.65 W[0.50, 0.78] |
| lossy@0.6 | descriptive | 0.82 B[0.74, 0.90] (n=96) | 84/96 = 0.88 W[0.79, 0.93] B[0.80, 0.94] | 38/40 = 0.95 W[0.83, 0.99] |
| lossy_padded@0.6 | descriptive | 0.85 B[0.78, 0.92] (n=96) | 88/96 = 0.92 W[0.84, 0.96] B[0.85, 0.97] | — |
| source_first@0.6 | descriptive | 0.70 B[0.60, 0.78] (n=96) | 68/96 = 0.71 W[0.61, 0.79] B[0.61, 0.80] | 27/40 = 0.68 W[0.52, 0.80] |
| lossy@0.3 | gated | 0.01 B[0.00, 0.03] (n=96) | 1/96 = 0.01 W[0.00, 0.06] B[0.00, 0.03] | 0/40 = 0.00 W[0.00, 0.09] |
| lossy_padded@0.3 | gated | 0.00 B[0.00, 0.00] (n=96) | 0/96 = 0.00 W[0.00, 0.04] B[0.00, 0.00] | 0/40 = 0.00 W[0.00, 0.09] |
| source_first@0.3 | gated | 0.99 B[0.97, 1.00] (n=96) | 96/96 = 1.00 W[0.96, 1.00] B[1.00, 1.00] | 40/40 = 1.00 W[0.91, 1.00] |
| lossy@0.1 | gated | 0.00 B[0.00, 0.00] (n=96) | 0/96 = 0.00 W[0.00, 0.04] B[0.00, 0.00] | 0/40 = 0.00 W[0.00, 0.09] |
| lossy_padded@0.1 | gated | 0.00 B[0.00, 0.00] (n=96) | 0/96 = 0.00 W[0.00, 0.04] B[0.00, 0.00] | 0/40 = 0.00 W[0.00, 0.09] |
| source_first@0.1 | gated | 0.99 B[0.97, 1.00] (n=96) | 96/96 = 1.00 W[0.96, 1.00] B[1.00, 1.00] | 40/40 = 1.00 W[0.91, 1.00] |

column labels (method / n / temperature / problem economy / arm):
- **paper-committed** — the arXiv v2 Table 5 values with the paper's own bootstrap brackets (B, verbatim; evidence/m3/paper-extraction.md), n=96 (32 fixed problems × 3 seeds), temperature 0.7 (the paper's caption, verbatim — NOT the released tool's 0.0 default); their problem economy (session 1 rebuilt per policy); directed arm.
- **their-harness-run** — our recount of their fix_*.jsonl rows; Wilson (W) and their own boot_ci (B) both computed from the same rows; their tool defaults (temperature 0 = our D10), their problem economy, directed arm.
- **ours** — archived judged-once cells (evidence/), Wilson, n=40–90, temperature 0, fresh problem per trial (D5), directed arm.

### Claim 3 beside their disposition table (labels carried per row)

- **deepseek** — ours: wrong-emission gap +58% [+44.2%, +67.5%] (lossy 52/90 vs blank 0/40, fresh problems, temp 0, arms sampled on different dates as pre-registered) · theirs: Δ+0.83 (n=96, their problems, their sweep config).
- **llama** — ours: probe NULL 1/12 vs 0/12 (+8% [-17%, +35%], n=12/arm, underpowered by pre-commitment — D17 rider a declined) · theirs: Δ+0.17 — our probe interval already contains their value.
- **qwen** — theirs: qwen-2.5-7b Δ+0.39 — **no comparable cell**: our slot ran qwen-2.5-72b-instruct, a same-family 10×-size substitute (D13's standing label), never presented as the paper's model. Our 72b probe: 0/12 vs 0/12 (abstainer NULL).

### D20 rider-a recount (archived lossy@0.1 wrong-emission splits, counted once at table time, gating nothing)

- **llama** lossy@0.1 wrong-emission 2/40 = 0.05 W[0.01, 0.17] (attractor 2, other 0, abstain 38, reclaimed 0) · their tab:blank llama lossy-emit 0.17
- **qwen72b** lossy@0.1 wrong-emission 1/40 = 0.03 W[0.00, 0.13] (attractor 0, other 1, abstain 39, reclaimed 0)

footnotes — the protocol findings:
1. their `reproduce_tables.py` exits nonzero on the public repo (it ships an empty data/results/ directory) — the "every table reproduces from committed results" claim fails on the artifact as shipped (M0 finding, reconfirmed in M3).
2. their `parse_answer` wrap set has no backslash escape, so `ANSWER: \$197` reads as an abstention — their deepseek/qwen cells may under-read escaped commits as abstentions. An under-read on the lossy arm can only SHRINK a lossy−blank emission gap, so their deepseek Δ+0.83 would be a floor, not an artifact, if it bit at all. their parse_answer read 0/8 archived escaped ANSWER lines as commits (every one carries a real committed value; ours reads all 8); plain controls agree 4/4.
3. whether it moved their published numbers is unknowable from their committed artifacts (no raw replies in their rows).
4. the paper v2 and their repo README's Findings table disagree in the last digit on three wall cells (paper lossy@0.3 0.01, sf 0.99/0.99 vs README 0.00, 0.96/1.00) — both are the author's numbers; this table carries the paper's committed values and records the variance here.

### D21 — the bootstrap robustness appendix

`uv run bootstrap.py appendix` over the archived record: **39 rows (every gated cell
rate and gap in claims 1–3), zero gate disagreements** — the interval-method choice
never drove a verdict (`evidence/m3/bootstrap-appendix.txt`). The 0/n degeneracy showed
exactly as the brief named it in advance: every all-zero cell's bootstrap collapses to
[0.000, 0.000] beside Wilson's honest [0, 8.8%] — false certainty at the extremes, the
reason D4 made Wilson the decider. Their `boot_ci` was re-typed verbatim (B=5,000,
seed 0, percentile) with reference-stream tests pinning the exact draws.

### D22 — the capstone

`docs/figs/capstone.png` — one self-contained figure: the knob curves per model
(padded points and deepseek's blank point at the wall), claim 3's emission bars
(52/90 vs 0/40), and the cross-check panel (ours · their-run · paper-committed on the
six llama wall cells, visibly on top of each other). Built entirely from archived rows
plus the oracle run, $0 new spend. `m1-wall.png` / `m2-knob.png` / `m2-emission.png`
stay untouched as milestone records.

### Cost ledger (their runner's token-measured cost at OpenRouter list prices)

| item | cost |
|---|---|
| oracle probe (1 call, slug + per-call cost) | <$0.001 |
| seed-1 smoke (96 units, 1,632 calls, 823,911 tok) | $0.018 |
| `--seeds 3` resume (192 units, 3,264 calls, 1,670,087 tok) | $0.037 |
| free items (fixture, dumps, extraction, judge, table, capstone, appendix) | $0 |
| **M3 total** | **≈ $0.056 measured** |

Far inside the brief's base envelope ($0.10–0.15; hard ceiling $0.35 — no contingency
fired). **Running project total ≈ $0.97** of KICKOFF's "likely under $10." The binding
constraint was, as predicted, wall-clock: ~7.6h of serial background hum on a slow
provider day.

### Exit criteria checklist

- [x] a cross-check verdict recorded with all six cells' intervals, judged only by the
      pre-committed criterion (AGREE — table above; `evidence/m3/m3-agreement-judge.txt`)
- [x] the comparison table committed with every column labeled and both protocol
      findings footnoted (above)
- [x] `bootstrap.py` green with the appendix committed; zero Wilson-vs-bootstrap
      disagreements to flag (`evidence/m3/bootstrap-appendix.txt`)
- [x] the capstone figure committed (`docs/figs/capstone.png`)
- [x] the README story rewritten under the pre-committed D20 mapping
- [x] the M3 checkpoint documented (recount + spot-check + cost, above)
- [x] evidence committed per D15 (`evidence/m3/`, 18 files incl. their 2,304-row
      checkpoint JSONL, key-scan clean)
- [x] measured M3 cost in the ledger (above)
- [x] spine updates in the same PR as the closing code (this PR: ROADMAP.md,
      DECISIONS.md D19–D22 outcomes, LEARNING.md M3, README verdict story)

### The post-v1 fork (decision brief — Kyle picks; nothing here is decided)

v1 is complete: every pre-registered claim judged, the cross-check AGREE, one legible
deliverable shipped. KICKOFF gated two extensions on "the effect shows" — it showed —
so the gate CONDITION is met and the decision is now live:

- **A. Close v1 and run `/seed-hunt` (Recommended).** *Merits:* v1's deliverable — one
  legible, defensible replication with a capstone — is done; the lineage's learning
  compounds fastest on a fresh paper (forge-gap → decay-pin → lossy-wall each taught a
  new methodology layer); the remaining extensions deepen breadth on a result that is
  already decisive 3-for-3. *Trade-off:* the logic family's softer wall (paper: 0.25
  vs 0.67 at the wall, not 0.00 vs 1.00) stays unmeasured here — the one place a
  partial/null was ever plausible.
- **B. Open M4 (the logic family).** *Merits:* the paper's second task family, where
  the wall is soft — the most likely place to find a PARTIAL verdict and therefore the
  most falsification-shaped extension; the harness needs only a new problems generator
  + templates (their `problems.py` logic set as protocol reference). *Trade-off:* a
  second full grid's spend and evenings on a project whose headline is already earned;
  the softer wall needs bigger N for the same CI discipline (mid-range rates are
  noisier than 0% and 100%).
- **C. Open M5 (the source-size boundary arm).** *Merits:* measures WHERE the wall
  sits (how much source must survive), a mechanism question v1 never touched.
  *Trade-off:* a new axis (source-fraction sweep) means new pre-commitments from
  scratch; the paper's own boundary section is thinner, so the comparison anchor is
  weaker.

*Why A:* the project's stated job (KICKOFF) was reproduce-and-measure with the honest
framing, not exhaustive coverage; that job is finished and the verdict table is the
artifact. M4/M5 stay gated-open in KICKOFF's terms — a future session can pick B or C
without re-arguing scope — but the recommended move is to bank v1 and point the
selection bar at the next paper.

**Outcome (2026-07-08):** Kyle picked **B — open M4, the logic family**. Start-of-stage
brief written and signed the same day (`docs/M4-BRIEF.md`, PR #22): **D23-A** core scope,
**D24-A** logic drift-take pilot, **D25-A** soft-wall gates (gap-gates claim 1,
separation-gates claim 2, recov/inherit/novel/abst taxonomy, verdict mapping pre-committed),
**D26-A** N=60 flat; riders (a) arXiv logic extraction and (b) taxonomy readout both yes. M5
stays gated-open, not denied. M4 progress tracked in the table above; the milestone's close-out
section will land here at M4 close.

---

## M4 — the logic family (the soft wall) · CLOSED 2026-07-08 · **PARTIAL**

**Verdict: claim 1 (fix generalizes) PARTIAL; claim 2 (content, not length) PARTIAL.** Judged
once at N=60 under D25's pre-committed gap/separation mapping. The brittle-memory fix generalizes
to logic **decisively on deepseek**, but the wall is soft and qwen's ordering cells are confounded
by a directed-correction interaction; with llama sat out (D24 trigger), that is one clean model of
the two the ≥2-model bar requires → PARTIAL. A genuine, well-characterised outcome — the most
falsification-shaped milestone in the project (KICKOFF flagged logic as the one place a
partial/null was plausible).

### The judged grid (N=60, directed, temperature 0.0; recov = reclaim)

| cell | deepseek | qwen72b | paper (llama, ref) |
|---|:--:|:--:|:--:|
| lossy@0.1 | 0.65 W[52.4, 75.8] | 0.75 W[62.8, 84.2] | 0.12 |
| lossy@0.3 | **0.23** W[14.4, 35.4] | 0.65 W[52.4, 75.8] | 0.25 |
| lossy_padded@0.1 | 0.72 | 0.75 | 0.04 |
| lossy_padded@0.3 | **0.07** | 0.48 | — |
| source_first@0.1 | **1.00** W[94.0, 100] | 0.72 W[59.2, 81.5] | 0.67 |
| source_first@0.3 | **1.00** W[94.0, 100] | 0.63 W[50.7, 74.4] | 0.67 |

**Claim-1 gap (sf − lossy), Newcombe 95%:** deepseek +35% [+22.6, +47.6] @g0.1, +77% [+63.2, +85.6]
@g0.3 — both exclude zero → **cleared**. qwen −3% [−18.8, +12.4], −2% [−18.3, +15.1] — straddle
zero → **not cleared**. **Claim-2 separation (sf − padded):** deepseek +28%, +93% (cleared); qwen
−3%, +15% (not cleared). Equivalence (padded − lossy) reported descriptively, never gated
(δ=0.10 unpowerable at N=60 on a mid-range rate — D25).

### The two substantive findings

- **Worse-than-empty, on deepseek's lossy floor (the thesis, on logic).** lossy@0.3 inherits the
  planted drift 27/60 (45%); *padded*@0.3 inherits 42/60 (70%) — padding the corrupted note to
  source length makes the error **stickier**, not safer. The g-inversion (lossy 0.65 at g=0.1 vs
  0.23 at g=0.3) is the mechanism: the barer g=0.1 note carries only the drift conclusion (model
  flips it via the correction → recovers), while the g=0.3 note keeps the *corrupted premise*
  (model reasons from it → inherits).
- **The directed correction × ordering-logic confound (the checkpoint's catch).** On ordering
  puzzles, the correction "the X-vs-Y order was wrong" reads as a flip instruction. qwen obeys it:
  in lossy it flips the bare drift conclusion → correct (lossy inflated to ~0.75); in source_first
  it flips the *true* fact → the drift (sf deflated to ~0.4; every sf error is `inherit`, `novel`=0).
  deepseek re-derives and resists it (sf 1.00). Stratified by type: on **assignment** puzzles both
  models show the effect cleanly (deepseek gap +0.67, qwen +0.83); the confound is entirely in the
  **ordering** stratum. The take-biased bank is ordering-heavy (deepseek banks only 3 assignment
  trials/cell — it rarely takes assignment drift), so a stratified 2-model test is underpowered;
  reported descriptively, not gated (Kyle's call, this session).

### Roster (D24 pilot) and the take-probe bug

The D24 logic drift-take pilot froze the grid roster **two-model** (deepseek AMBER 10/20, qwen72b
GREEN 15/20; **llama TRIGGER 9/20 → sits out**). llama's first pilot read a false 0/20 TRIGGER from
a take-probe format bug (`TAKE_PROBE_LOGIC` wasn't format-explicit → llama's bare-token drift commits
slipped the strict `ANSWER:` parser); the mandatory hand-read caught it, the fix (PR #28) restored
llama to its true 9/20, and the fidelity audit vs `experiment.py` confirmed the recipe faithful
(deepseek/qwen took on the same problems). llama's trigger is real; its abstainer disposition at the
wall (0/9 emit) matches v1. Anchor-out: scope B (llama·logic cross-check) moot; D25's REPRODUCED
anchored-shape clause not evaluable; the ≥2-model gap governed (Kyle, this session).

### M4 cost ledger (OpenRouter-measured)

| item | cost |
|---|:--:|
| D24 pilot (3×20 + wall reads) | $0.061 |
| llama re-pilot (corrected probe) | $0.002 |
| bank deepseek (60 taken / 115 trials) | $0.174 |
| bank qwen72b (60 taken / 83 trials) | $0.112 |
| grid@20 (checkpoint, both) | $0.028 |
| grid extend 20→60 (both) | $0.056 |
| free (extraction, judge, figure) | $0 |
| **M4 total** | **≈ $0.433 measured** |

The driver above the brief's mid-estimate was long logic prompts (8 accumulating follow-ups) and
deepseek's 52% take rate (115 trials to bank 60). **Running project total ≈ $1.40** of KICKOFF's
"likely under $10."

### Exit criteria checklist

- [x] claim-1 (gap) + claim-2 (separation) verdicts per surviving model per wall g, both arms'
      intervals, judged only by the pre-committed D25 mapping (above; `evidence/m4/judge.txt`)
- [x] soft-floor characterisation + four-way taxonomy + chance floor reported (above; figure)
- [x] D24 drift-take pilot verdicts recorded per model (D24 outcome; llama sits out)
- [x] the mandatory checkpoint hand-read documented (the confound diagnosis, above)
- [x] figure committed (`docs/figs/m4-logic-wall.png`)
- [x] evidence committed per D15 (`evidence/m4/`, 8 run JSONLs + judge + extraction)
- [x] measured M4 cost in the ledger (above)
- [x] spine updates in the same PR (this PR: ROADMAP M4, DECISIONS D24–D26 outcomes,
      LEARNING M4, README status, M4-BRIEF header)
- [ ] Kyle's answers to M4's three recall questions (LEARNING.md — open, as M3's remain)

M5 (source-size boundary arm) stays gated-open, not denied.

---

## M5 — the source-size boundary arm · complete 2026-07-09 · **REPRODUCED**

**Verdict: the source-size boundary REPRODUCED.** The `source_first` fix leads until the source
outgrows the note budget, then cliffs — and the cliff **tracks the budget, not problem size**, the
paper's central boundary claim. Judged at N=20 under D29's pre-committed gate (D30 amended from the
signed N=40: the 0/1 effect resolved decisively at 20, so extending was low-value spend — Kyle's
call at the checkpoint). Brief `docs/M5-BRIEF.md` (D27-A · deepseek/arithmetic); the free build +
the **D28 reopen** (rider-a extraction found the paper's design is grow-N-at-two-budgets, D28-B,
not the signed A) landed in PR #30. Decisions D27–D30 in `DECISIONS.md`; anchor record
`evidence/m5/paper-extraction-boundary.md`.

### The judged grid (N=20, directed, temperature 0.0; deepseek) — source_first reclaim

| source size N | 2 | 4 | 6 | 8 | 12 | 16 | crossover |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **B=300** | 20/20 | 20/20 | **0/20** | 0/20 | 0/20 | 0/20 | **N=4** (paper ≈5) |
| **B=600** | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 | **0/20** | **N=12** (paper ≈14) |

**Per-budget cliff (D29):** ceiling intact both budgets (20/20 at min N); drop RR@min−RR@max
**+100% [+48.4%, +100%]** both, excludes zero; monotone both. **Crossover tracks the budget: True**
(4 < 12) — and both crossovers bracket the paper's own anchors. **Mechanism (full k=N vs partial
k<N):** full **139/140** vs partial **0/108**, Δ**+99% [+94.6%, +99.9%]** — an exact sum needs
every item; the cliff is to 0.00 the instant one item is dropped.

### The three substantive findings

- **The silent mis-sum, on real deepseek (worse-than-empty).** Past the cliff `source_first` does
  not abstain — it confidently sums the *partial* source to a wrong total (`emit_other_wrong`,
  e.g. 5 of 8 items → a partial-sum figure). The checkpoint hand-read confirmed it is genuine
  recompute-failure, not a token-cap abstain or a parser artifact. `lossy_padded` (budget-matched
  to source_first's length) sits at 0/20 everywhere — the cliff is source *content*, not note length.
- **The crossover tracks the budget.** Doubling the budget (300 → 600) moves the crossover N=4 → 12.
  If the cliff were problem difficulty, it would sit at the same N regardless of budget; it does not.
- **Drift-take collapses at N=24 — the boundary of the boundary.** deepseek banks 20 taken easily to
  N=16 (take 53–95%) but only **4/48** at N=24: on a 24-item receipt it re-derives the correct total
  rather than accept the planted wrong subtotal. So N=24 is unmeasurable (dropped); the *take
  precondition* fails before the budget does at very large source size — a reported finding.

### M5 cost ledger (OpenRouter-measured)

| item | cost |
|---|:--:|
| banks to 20 taken × 7 sizes (N=2–24; N=24 short at 4/48) | $0.634 |
| grid: N×budget×policy to N=20 (496 s2 calls) | $0.092 |
| free (extraction, judge, figure) | $0 |
| **M5 total** | **≈ $0.726 measured** |

Over the brief's $0.4–0.6 estimate — 7 banks (not one), long multi-item prompts, and low-take
large-N receipts drove it; the estimate miss is noted. **Running project total ≈ $2.13** of
KICKOFF's "likely under $10." Figure: `docs/figs/m5-boundary.png` (source_first RR vs N per budget,
the two cliffs, the crossovers, the lossy_padded floor).

### Exit criteria checklist

- [x] a cliff verdict judged only by the pre-committed D29 gate (REPRODUCED — table above;
      `evidence/m5/judge.txt`)
- [x] per-budget ceiling / drop / monotone + crossover-tracks-budget + full-vs-partial mechanism,
      all intervals recorded (above)
- [x] the silent mis-sum + lossy_padded floor + the N=24 take-collapse reported (above)
- [x] the mandatory N=20 checkpoint hand-read documented (no scoring bug; genuine mis-sum)
- [x] figure committed (`docs/figs/m5-boundary.png`)
- [x] evidence committed per D15 (`evidence/m5/`: banks, grid, judge, extraction; key-scan clean)
- [x] measured M5 cost in the ledger (above)
- [x] spine updates in the same PR (this PR: ROADMAP M5, DECISIONS D27–D30 outcomes, LEARNING M5,
      README status, M5-BRIEF header)
