# ROADMAP.md — milestone status

Scope source of truth: `docs/KICKOFF.md` (phased plan + gate record). Decisions live in
`DECISIONS.md`; teaching notes in `LEARNING.md`; per-stage briefs in `docs/`.

| Milestone | What it is | Status |
|---|---|---|
| **M0 — the fit-pilot** | de-risk: machinery + drift-take pilot + disposition probe | **complete (2026-07-06)** |
| M1 — the wall | lossy vs source_first @ g=0.1/0.3, claim 1, wall figure | next — needs its start-of-stage brief |
| M2 — the controls | lossy_padded (claim 2) + blank/emission (claim 3), knob fills | pending |
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
| deepseek-chat | 13/20 | 65% | [43%, 82%] | **AMBER** — proceed; session-1 generation inflated ~1/0.65 ≈ 1.5×; weak take noted in README |
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
| deepseek | 10/12 | 0/12 | +10 | [+46%, +95%] | **GREEN** — claim 3 measurable at M2's N≈40 |
| qwen-7b | — | — | — | — | skipped: D8 trigger fired (probe runs on survivors only) |
| qwen-72b | — | — | — | — | deferred with its pilot (M1 brief) |

The headline: deepseek reproduces the title claim's shape at full strength — holding a
lossy note at the wall it confidently emits wrong values (6 attractor re-emissions + 4
other-wrong of 12), while with a blank memory it abstains 12/12. Both riskiest
assumptions (drift takes; the gap is powerable at hobby N) are answered YES.

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
