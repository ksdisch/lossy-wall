# M1 Start-of-Stage Brief — the wall

*Written 2026-07-07 · status: **awaiting sign-off** — D13–D15 proposed below; no M1 code
and no paid call until Kyle signs · scope source of truth: `docs/KICKOFF.md` (Milestone 1)
· format follows `docs/M0-BRIEF.md`.*

## What M1 is, in plain terms

M0 proved the machinery works and the preconditions hold. M1 is the first milestone that
measures the headline itself: **the wall** — KICKOFF claim 1.

The claim under test: once compression has dropped a note's *source* (the ledger's line
items — the material you'd need to recompute the answer) and kept only its *conclusion*
(the wrong total the model committed to), a directed correction stops working. The model
holding that lossy note can't reclaim — its **reclaim rate** (RR: the fraction of trials
where the model, told exactly where the error is, commits the *correct* total on its
ANSWER line) sits at ~0. Spend the same character budget **source-first** — keep the line
items, drop the recomputable conclusion — and the correction works essentially every
time. The paper's numbers at wall integrity: RR 0.00 (lossy) vs 0.99–1.00 (source_first).

Everything M1 needs already exists from M0 except the grid driver: both note policies are
pure functions in `notes.py`, every note passes the per-trial source gate *in both
directions* before a trial may run (`runner.verify_note_gate`: a lossy wall note must
demonstrably LACK the source, a source_first note must CARRY it), the ANSWER-line grader
is the same strict parser everywhere, and session 2 is the paper's exact
`[system, note, directed correction]` frame. So M1 is: build the trajectory bank, run an
8-cell grid, judge a pre-committed gate, draw the wall figure.

**The grid** (per model): 2 policies (lossy, source_first) × 2 wall integrities
(g = 0.1, 0.3), directed corrections only (D2). Roster: llama + deepseek (M0 survivors),
with the third slot decided by D13 below. A **cell** is one (model × policy × g)
combination measured over N independent trials.

One new measurement risk is genuinely open: **M0 never ran source_first** (the D9 probe
was lossy vs blank). The paper says source_first reclaims at 0.99–1.00; if our build
reads much lower, the first suspect is protocol drift on our side, not the paper — which
is why the checkpoint below hand-reads source_first trajectories before the grid scales
up.

## What M0 settled that M1 stands on

- **Roster and generation costs.** llama took 14/20 (D8 green — plan session-1
  generation at its measured take rate t̂ = 0.70); deepseek took 13/20 (D8 amber — its
  session-1 generation runs **inflated ×1/0.65 ≈ 1.54, a standing D8 mandate**, and the
  weak take is already noted in the README). qwen-2.5-7b fired its trigger and left the
  roster; the 72b substitute's pilot was infrastructure-blocked at 4 trials (3 takes) —
  resolving that slot is D13, and it happens **before** any grid call so the roster is
  frozen for the whole milestone.
- **Sampling and readout are decided, not re-decided.** Temperature 0.0 / max_tokens 600
  (D10) — the M1 driver **imports `TEMPERATURE` / `MAX_TOKENS` from `m0.py`**, never
  redefines them. Every bank trajectory ends with the take-probe measurement turn (D11),
  which is never carried into session 2. Trials condition on take (only taken
  trajectories feed session 2), per D8.
- **The M0 scoring lesson binds every new readout.** The anti-rig suite validates
  *mechanics*, not model behavior: two live scoring bugs (the cents-unit trap; llama
  committing values in prose without ANSWER lines) sailed through the deterministic fake
  and were caught only by hand-reading real trajectories. M1's readout (RR = the grader's
  `reclaimed` outcome) therefore gets a **mandatory hand-read checkpoint** before any
  cell scales past N=20 — built into the gate schedule below.
- **A fresh discovery from this handoff: the container ate the evidence.** This session
  runs in a new machine, and `runs/` (M0's trial-by-trial JSONLs), `.env`, `uv.lock`,
  and `docs/session-logs/` — all gitignored or never committed — did not survive.
  M0's verdict *tables* are safe in `ROADMAP.md`, but the raw evidence behind them is,
  as far as this machine can see, gone. That convention gets fixed before M1 spends
  anything: D15.
- **Not re-litigated here:** M0's verdicts, D1–D12, the v1 scope. Settled.

## The design: one bank, eight cells, one figure

**The trajectory bank.** A *trajectory bank* is a pool of taken session-1 trajectories —
conversations where the model demonstrably committed to the planted wrong total — that
all downstream cells draw from. D5's pairing makes this natural: the four note policies
are write-time transformations of the *same* session-1 trace, so ONE taken trajectory
feeds every policy × g cell for that trial. M1 builds the bank; the grid consumes it.

- Fresh problem per trial (D5), on a new `m1-` seed schedule, **shared across models**
  (m0.py's paired design: every model sees the same problems, so differences are the
  model's, never the problem draw's). M0's pilot problems are not reused.
- Bank target: **40 taken per model** up front (the design N below), generated at
  1/t̂ inflation — ≈ 58 raw trajectories for llama, ≈ 62 for deepseek — with m0.py's
  top-up pattern if takes run short. ~10 calls per trajectory (plant + 8 follow-ups +
  take-probe).
- Full trajectories are logged as JSONL, per M0 convention — and under D15 they get
  **committed** at milestone close. That makes the bank a durable asset: M2 reuses these
  exact trajectories for its lossy_padded / blank / knob cells (the g=1.0 lossy cell
  carries the full transcript, so the saved trajectories are literally M2's input), even
  from a fresh container.

**The grid.** Per model, per cell: session 2 = `[system, note, directed correction]`,
one call per trial, note gated per trial in the right direction, reply graded by the
strict parser. RR is the count of `reclaimed` outcomes over N. Everything logged
(`policy, g, note, reply, parsed, hedged, outcome, temperature, cost`) exactly like
m0.py's probe rows, under `runs/m1-<cell>/`.

**A quiet protocol fact worth knowing (it's in the paper's design too):** the g mapping
is a *threshold*, so at both wall values source_first produces the **identical note
string** ("facts only, conclusion dropped"). Our sf@0.1 and sf@0.3 cells are therefore
two independent samples of the *same condition* — we run both anyway (paper-faithful
bookkeeping, keeps each g row internally paired, and costs pennies), and their agreement
is a free consistency check: if two samples of the same condition disagree beyond noise,
something is wrong with the run, and we stop and look. The lossy side is NOT degenerate:
at g=0.3 the note carries premise + wrong conclusion, at g=0.1 the conclusion only — the
wall has internal structure on the lossy side and none on the source side.

**The wall figure** (`docs/figs/m1-wall.png`, committed): reclaim rate vs g, one panel
per model, two series (lossy, source_first) with Wilson 95% error bars and per-point N
annotated; x-axis laid out for the full knob {0.1, 0.3, 0.6, 1.0} so M2's cells drop
into the same figure without rework.

## The claim-1 gate, mechanically

KICKOFF claim 1 has two components, judged per (model, g) cell pair with the settled
stats (D4):

1. **The lossy ceiling** — the lossy cell's Wilson 95% CI is "consistent with ~0".
   KICKOFF left "~0" to be operationalized here; that's **D14**, the ceiling on the
   Wilson *upper bound* (a one-sided bar: "even at the unlucky edge of the interval, the
   true rate is at most X").
2. **The gap** — the Newcombe 95% interval on (source_first − lossy) excludes zero.

Pre-committed composition, before any data exists:

- A model **clears claim 1** only if BOTH components hold at BOTH wall integrities
  (g = 0.1 and 0.3). One-g-only is reported as PARTIAL with the boundary noted — that's
  potential structure (where the wall starts), not a pass.
- **v1 clears claim 1** if ≥ 2 models of the final roster clear (KICKOFF's "≥2 of 3");
  on a two-model roster that means both. One-model-only → PARTIAL, reported plainly.
- Wilson/Newcombe decide (D4); every judged interval lands in ROADMAP's verdict table.
- The N schedule (start at 20, judge at 40, one pre-committed escalation) is D14's
  option ladder below — including the **checkpoint**: a scheduled interim look at N=20
  whose ONLY powers are bug-catching (hand-read) and futility stops. No claim can be
  *cleared* at the checkpoint, so peeking can't flatter the result — the gate is judged
  once, at final N.

## Decisions — pick or veto (recommendation marked; numbering continues DECISIONS.md)

### D13 · The third-model slot: one bounded 72b re-attempt, then the roster freezes

Where it stands: qwen-2.5-7b is out (D8 trigger, D12). Kyle's substitute,
qwen-2.5-72b-instruct, is route-pinned to DeepInfra and its pilot was
infrastructure-blocked twice on 2026-07-06 (throttled past 8 SDK retries) with 3/4 takes
on the trials that ran — promising, unproven.

- **A. One bounded re-attempt now, before any grid call (Recommended).** Re-run
  `uv run m0.py pilot 20 qwen72b` once (≈ $0.06 at its measured per-trial cost). If it
  completes: apply D8's tiers as written; green/amber → run its D9 probe
  (`uv run m0.py probe 12 qwen72b`, ≈ $0.01) and 72b joins M1's grid as a third model —
  labeled in every table as a same-family, 10×-size substitution, never as the paper's
  qwen-7b. If it infrastructure-fails again (throttle/400 past the adapter's retries):
  **v1 closes two-model permanently** — no further attempts in any later milestone, no
  direct-provider accounts for a nice-to-have. *Merit:* ~$0.06 buys a final answer
  either way, and the roster freezes before the milestone starts. *Trade-off:* if 72b
  joins, M1's cost and wall-clock grow ~50%, and the pilot+probe add ~an hour before
  the grid.
- **B. Defer the re-attempt to M2.** *Merit:* M1 starts immediately. *Trade-off:* a
  third model joining at M2 would have no M1 claim-1 cells — backfilling them later
  (running cells out-of-milestone after their gate was judged) splits the "judge once"
  discipline, and the dangling thread survives another milestone.
- **C. Close two-model now, no re-attempt.** *Merit:* simplest. *Trade-off:* abandons a
  3/4-take pilot that $0.06 would finish, and the qwen family — the roster's second
  model family — exits the study on an infrastructure accident rather than a verdict.

*Why A:* it's the only option that terminates the thread today at known cost, and both
outcomes are useful — a third family strengthens "≥2 of 3", a clean close is honest.
KICKOFF's success criteria are already satisfiable two-model, so this is upside, not
need.

### D14 · "Consistent with ~0": the ceiling and the escalation ladder

The choice that makes claim 1 judgeable. Context for all options: a Wilson 95% upper
bound at small N is never tiny — a perfect 0/20 still reads "up to 16.1%", 0/40 reads
"up to 8.8%" — so the ceiling and the N schedule have to be chosen together. (All bounds
below computed with our `stats.py`.)

- **A. Ceiling 0.10, judged at N=40, with D7's escalate-on-a-stray to N=90
  (Recommended).** One project-wide meaning of "small": the same ±10 points that D7
  committed for claim 2's equivalence band. Schedule, per cell:
  - Every M1 cell runs to **N=20**, then stops for the **checkpoint**: hand-read ≥3
    randomly picked trials per cell against the raw logs (the M0 lesson — eyes on real
    replies before trusting counts; an advisory eye on source_first: if its RR reads
    surprisingly low, audit protocol fidelity before spending further), plus a futility
    screen. Nothing can clear at 20 (0/20's bound is 16.1% > 0.10 by construction) —
    the checkpoint only kills or continues.
  - Cells then extend to **N=40** and the gate is judged. Lossy ceiling at 40:
    **0/40 (bound 8.8%) clears**; 1–3 reclaims (bounds 12.9–19.9%) → the cell
    **escalates once to N≈90**, D7's exact idiom, where ≤3 total reclaims clears
    (3/90 → 9.3%); ≥4 reclaims at any point is final — no N ≤ 90 can pass
    (4/90 → 10.9%), so the cell stops as not-cleared. Futility at the 20-checkpoint is
    the same rule: ≥4 reclaims at 20 → not-cleared, stop spending.
  - source_first cells always stop at N=40 (no ceiling applies to them); the Newcombe
    gap is judged once, when its two cells reach their final Ns (unequal n is fine).
  *Merit:* strictest defensible bar, symmetric with D7 — one "smallness" scale across
  the whole project — and the expensive path (N=90) triggers only when the data
  actually shows a stray reclaim. *Trade-off:* a single stray costs that model a bank
  top-up to ~90 taken (~$0.15, reused by M2) and ~50 more session-2 calls.
- **B. Ceiling 0.15, judged once at N=40, no escalation.** 0/40 and 1/40 clear; ≥2 is
  final. (Futility at the checkpoint: ≥2 reclaims at 20.) *Merit:* simpler, cheapest,
  tolerates one stray without more spend. *Trade-off:* "at most ~1-in-7" is a loose
  reading of the paper's 0.00, and the project would carry two different smallness
  bars (0.15 here, 0.10 in D7) — a fair "why the difference?" from a careful reader.
- **C. No ceiling — gate on the Newcombe gap alone.** *Merit:* one fewer number.
  *Trade-off:* drops half of KICKOFF's pre-registered claim (a 30%-reclaim lossy cell
  could pass on gap alone, and "the wall pins lossy near zero" is the finding).
  Rejected unless Kyle overrules.

*Why A:* pre-commitment is worth most where the temptation to bend would be strongest —
at the headline. A stray reclaim under option A doesn't kill the claim OR get waved
through; it buys a bigger sample, exactly like D7. And ≥4 lossy reclaims failing the
gate is itself a *reportable* structure finding (the paper says 0.00; we'd be measuring
≥10% — DISCREPANT territory for M3's verdict table, not a shrug).

### D15 · Run evidence must survive the machine (+ two riders)

M0's raw evidence is gone with the old container (summary tables survive in ROADMAP.md).
The convention that allowed that — `runs/` gitignored, nothing archived — contradicts
what this repo is for: a replication whose verdicts a stranger can audit.

- **A. Commit paid-run evidence per milestone (Recommended).** `runs/` stays gitignored
  as the working directory; a milestone's **closing PR copies its JSONLs into
  `evidence/m1/` (etc.) and commits them** — full trajectories + results rows, text
  JSONL, order-of-1 MB per milestone in a public repo. The bank's committed
  trajectories are also what M2 consumes (see design above), so this is
  reproducibility + M2's input in one move. *Trade-off:* repo weight grows a little
  each milestone.
- **B. Keep gitignored; Kyle archives manually.** *Merit:* repo stays lean.
  *Trade-off:* exactly the convention that just lost M0's evidence.
- **C. External storage (release assets / gist).** *Merit:* lean repo, evidence kept.
  *Trade-off:* more moving parts than a ~1 MB problem deserves, and auditability
  shouldn't require a second location.

*Why A:* the whole methodology stands on auditable trials (per-trial gates, hand-read
checkpoints); evidence that evaporates on container reclaim makes those guarantees
unverifiable after the fact. This is the cheapest possible fix.

**Riders (yes/no each, recorded with D15):**
- **(a) Commit `uv.lock` (recommended: yes).** Standard for applications (this repo is
  one, `package = false`): the lockfile pins the exact dependency versions runs used,
  so "works here" means something. The old container's lockfile is lost; the first M1
  code PR regenerates and commits it.
- **(b) Keep `docs/session-logs/` text-committed; gitignore media (recommended: yes).**
  The spine says raw session logs go there — text logs should be committed like the
  rest of the docs (and would then survive containers). The ~4 MB M0 audio memo should
  never enter git: add `docs/session-logs/*.mp3` (and kin) to `.gitignore`. The M0 text
  log + mp3 were never committed and are presumed lost with the old container — if
  Kyle still has copies, the text log gets committed, the mp3 stays local.

## M1 task list, free-before-paid, exit criteria

Order matters: **nothing paid runs until every free check is green**, and the roster
freezes before the first grid call.

1. **Sign-off** on D13–D15 (this brief). Restore `.env` (the container swap lost it —
   Kyle's key, never committed).
2. **D13 resolution** (if A): the one bounded 72b pilot re-attempt + probe; record the
   outcome in DECISIONS.md either way; roster frozen.
3. **Build `m1.py` + `test_m1.py`, TDD, $0:** bank builder (fresh `m1-` schedule shared
   across models, take-probe per D11, top-up per m0.py's pattern, JSONL logs); grid
   runner over `runner.run_session2(..., arm="directed")` with the per-trial gate; the
   **D14 ladder encoded as pure functions with unit tests** (m0.py's D8/D9 pattern:
   verdicts pre-committed in code, so they can't bend after data arrives); figure
   subcommand. Constants imported from m0.py (D10). Full pytest green before any paid
   call.
4. **Banks** to 40 taken per model (background, models in parallel; ≈ 25–40 min each).
5. **Grid to N=20 per cell → the checkpoint:** hand-read ≥3 trials per cell from the
   raw JSONLs; futility screen per D14; record what was read and seen (goes in the
   closing PR / LEARNING.md).
6. **Extend to N=40; judge the gate** per the D14 ladder (escalate a lossy cell to 90
   only as the ladder dictates); verdict table with every interval into ROADMAP.md.
7. **Wall figure** committed (`docs/figs/m1-wall.png`).
8. **Evidence + ledger + spine close-out, same PR:** copy `runs/` JSONLs to
   `evidence/m1/` (D15); measured cost ledger appended to ROADMAP.md; D13–D15 outcomes
   into DECISIONS.md; LEARNING.md M1 teaching note + new words + 3 recall questions;
   README status updated.

**Exit criteria:** a claim-1 verdict per model per wall g with both components'
intervals recorded, judged only by the pre-committed ladder; the checkpoint hand-read
documented; the wall figure committed; evidence committed per D15; measured M1 cost in
the ledger; all spine updates in the closing PR (definition of done).

## Cost and wall-clock (from ROADMAP's measured numbers)

Measured unit costs from M0: ≈ $0.0012 per session-1 trajectory (~10 calls, blended
across the trio), ≈ $0.00006 per session-2 call; 72b runs ≈ $0.0026 per trajectory.
Planning numbers below use ~1.5–2× headroom on the blend (deepseek-heavy mix).

| item | calls (approx) | estimate |
|---|---|---|
| banks to 40 taken (llama 58 + deepseek 62 raw trajectories) | ~1,200 | ~$0.15–0.25 |
| grid, 8 cells × N=40 session-2 | 320 | ~$0.02–0.03 |
| **base M1 (two-model)** | ~1,500 | **≈ $0.20–0.30** |
| worst case: every lossy cell escalates (banks → 90 taken, +200 s2 calls) | +~1,700 | ≤ ~$0.75 total |
| D13-A re-attempt (pilot 20 + probe 12 on 72b) | ~230 | ~$0.07 |
| D13-A if 72b joins the grid (bank + cells, at its pricier rate) | ~700 | +$0.20–0.45 |

Hard ceiling with a third model and every escalation: ≈ $1.2. ROADMAP's full-v1
extrapolation ($2–4) stands. The binding constraint remains statistics, not cost.

Wall-clock: banks ≈ 25–40 min per model, run in the background in parallel (M0's
pattern; every arm except 72b stayed under 10 min per 20-trajectory batch); grid sweeps
≈ 5–10 min per model; the checkpoint hand-read is human time (~20–30 min). One evening,
plus this sign-off.

## Explicitly NOT in M1

- lossy_padded and blank arms, claims 2 and 3, and the g = 1.0 / 0.6 knob fills — M2
  (δ = 0.10 already stands, D7).
- `bootstrap.py`, the paper-comparison table, the cross-check cell — M3.
- The logic family and the boundary arm — gated post-v1 (D2).
- Undirected/generic corrections in paid cells (validator-only, D2), any new task
  family, any roster change beyond D13, any re-litigation of M0 verdicts.

## Open items carried from M0 (same sign-off, no new numbers)

- If any copy of M0's `runs/` JSONLs or the session log (text or mp3) survives on
  Kyle's machine or the old container, drop the JSONLs into `evidence/m0/` and commit
  the text log per D15 — otherwise ROADMAP's tables remain M0's record, noted plainly.
- Kyle's answers to M0's three recall questions (optional, from the close of last
  session).

## New words introduced here

- **Trajectory bank** — the pool of taken session-1 conversations that every downstream
  cell draws notes from; built once, reused across policies, g values, and milestones
  (D5's pairing made durable).
- **Checkpoint / interim look** — a *scheduled* pause at N=20 to hand-read raw trials
  and apply futility rules, pre-committed so that looking early can never flatter the
  result (nothing can be *cleared* there, only stopped).
- **Futility stop** — ending a cell early because no remaining outcome could pass its
  gate (e.g. 4 lossy reclaims: even 4/90 breaches a 0.10 ceiling) — saves money and
  can only prevent false positives, never create them.
- **Ceiling** — a pre-committed bar on the Wilson *upper* bound: "even at the unlucky
  edge of the interval, the true rate is at most X" — how "consistent with ~0" becomes
  mechanical.
- **Replicate cells** — two cells that are the same condition by construction (our
  source_first pair at g = 0.1/0.3, identical note strings under the threshold
  mapping); their agreement is a free sanity check on the run itself.
- **Backfill** — running a cell after its milestone's gate was already judged (what
  D13-B would eventually force); avoided because judging once, on a frozen design, is
  what makes a gate a gate.
