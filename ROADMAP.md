# ROADMAP.md — milestone status

Scope source of truth: `docs/KICKOFF.md` (phased plan + gate record). Decisions live in
`DECISIONS.md`; teaching notes in `LEARNING.md`; per-stage briefs in `docs/`.

| Milestone | What it is | Status |
|---|---|---|
| **M0 — the fit-pilot** | de-risk: machinery + drift-take pilot + disposition probe | **complete (2026-07-06)** |
| M1 — the wall | lossy vs source_first @ g=0.1/0.3, claim 1, wall figure | **complete (2026-07-06)** — claim 1 CLEARED, 3/3 models |
| M2 — the controls | lossy_padded (claim 2) + blank/emission (claim 3), knob fills | **complete (2026-07-07)** — claim 2 CLEARED 3/3, claim 3 CLEARED (deepseek) |
| M3 — cross-check + capstone | author's harness on the overlap cell, comparison table, capstone | pending |
| M4 — logic family | gated post-v1 (only if the effect shows) | gated |
| M5 — boundary arm | gated post-v1 | gated |

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
