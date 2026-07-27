# Methodology-Guardrails

## Purpose
Answers "what honesty machinery did this project run on, and why was each piece chosen?"
for a reader who wants to understand or reuse the pre-registration, statistical, and
code-level disciplines. Synthesises across `DECISIONS.md` (D1–D22), `LEARNING.md`,
`stats.py`, `docs/KICKOFF.md`, and the per-milestone briefs — the full picture only
emerges from all of them together.

## Key understanding

### The core commitment: pre-registration before any paid call

**Decision** — D4, [`DECISIONS.md`](../DECISIONS.md): Wilson/Newcombe decide every gate;
bootstrap is robustness-only. Committed at the kickoff interview, 2026-07-06.

**Decision** — D7, [`DECISIONS.md`](../DECISIONS.md): equivalence margin δ = 0.10
for claim 2, committed before the project's first paid call.

**Decision** — D14, [`DECISIONS.md`](../DECISIONS.md): claim 1's ladder — ceiling 0.10
on Wilson-95 upper bound, checkpoint at N=20, judge at N=40, one escalation to N≈90,
≥4 reclaims is a final failure at any N. Written as pure functions in `m1.py` before
any wall-cell data existed.

**Inference** — the pattern across D4, D7, D8, D9, D14, D16, D17, D20, D25, D29 is
consistent: every decision that could be coloured by seeing results was fixed in the
ledger before the relevant data existed. This is the project's version of
pre-registration; the decision IDs + dates are the audit trail. Rests on reading all
D1–D30 entry dates in [`DECISIONS.md`](../DECISIONS.md).

### The statistical method: Wilson/Newcombe and why

**Fact** — `stats.py` exports exactly two functions, `wilson(k, n)` and
`newcombe_diff(k_base, n_base, k_mech, n_mech)`, plus a helper `excludes_zero(lo, hi)`.
The module docstring explains why: a reclaim rate is a proportion; ±std intervals can
escape [0, 1]; Wilson intervals stay honest at small N and near 0%/100%, which is
exactly where wall cells live. Source: [`stats.py`](../stats.py) lines 1–32.

**Fact** — `stats.py` is ported near-verbatim from decay-pin (the prior project in the
lineage); the module docstring says so. Source: [`stats.py`](../stats.py) line 1.

**Fact** — claim 1 uses `newcombe_diff(base=lossy, mech=source_first)` and tests
`excludes_zero`; claim 3 uses `newcombe_diff(base=blank, mech=lossy)` and tests
`excludes_zero`; claim 2 uses the same interval but tests containment inside ±δ = ±0.10
rather than `excludes_zero` — the module docstring names this distinction explicitly.
Source: [`stats.py`](../stats.py) lines 19–25 and the `newcombe_diff` docstring.

**Decision** — D4, [`DECISIONS.md`](../DECISIONS.md): the bootstrap appendix was added
specifically because the paper reports bootstrap CIs, making the comparison table honest.
Zero Wilson-vs-bootstrap gate disagreements were found across all 39 gated rows.
Source: [`ROADMAP.md` M3 D21](../ROADMAP.md).

**Fact** — the degenerate-interval problem was predicted in the D4/D21 brief and then
observed: every 0/40 cell's bootstrap collapses to [0.000, 0.000] — false certainty —
while Wilson reports [0%, 8.8%], the honest bound. Source: [`LEARNING.md` M3](../LEARNING.md),
[`DECISIONS.md` D21 outcome](../DECISIONS.md).

### Claim-gate anatomy (two kinds of gate)

**Fact** — the project used two structurally different gate types, both implemented as
pure functions before any data:

1. **Excludes-zero gate** (difference is real): the Newcombe interval on (mech − base)
   must not straddle zero. Gates claims 1 and 3, the M4 gap, and the M5 cliff.
2. **Containment gate** (two arms are equivalent): the Newcombe interval on
   (lossy_padded − lossy) must sit entirely inside ±δ = ±0.10. Gates claim 2's
   first component. A gate that merely "includes zero" is not evidence of equivalence
   — you need the interval to fit *inside* the band.

Source: [`stats.py`](../stats.py) module docstring lines 15–25; [`DECISIONS.md`](../DECISIONS.md) D7, D14, D16.

**Fact** — `excludes_zero` in `stats.py` is the single shared test for all
excludes-zero gates across the project; `m2.judge` uses the containment check for
claim 2. The gates are literal code, not judgment. Source: [`stats.py`](../stats.py) line 87–97.

### Pre-committed verdict vocabulary

**Decision** — D1, [`DECISIONS.md`](../DECISIONS.md): four verdicts committed at the
kickoff, before any data: REPRODUCED / PARTIAL / NULL / DISCREPANT. A null is a
reportable verdict, not a failure.

**Decision** — D20, [`DECISIONS.md`](../DECISIONS.md): the cross-check produces a
separate protocol-fidelity line (AGREE / DISCREPANT) that sits beside claim verdicts
rather than overriding them. Claim verdicts stand as judged even if the cross-check
were DISCREPANT.

**Decision** — D25, [`DECISIONS.md`](../DECISIONS.md): the M4 verdict mapping (gap-gates
claim 1, separation-gates claim 2) was adapted before any logic data because the
arithmetic ceiling (≤0.10) is false-by-the-paper on the logic family. Honesty required
a gate that tests what's actually testable, not the gate from a different task family.

### Scored-once and no-rerun discipline

**Decision** — D5, [`DECISIONS.md`](../DECISIONS.md): fresh generated problems per trial
(not the paper's 8-problems × 3-seeds reuse) so Wilson's independence assumption holds.

**Decision** — D15, [`DECISIONS.md`](../DECISIONS.md): per-milestone evidence committed
to `evidence/<milestone>/` (JSONLs) so verdicts are auditable and escalation re-scores
are possible on archived data. This saved the project when a parser bug was found: M0's
deepseek verdict was re-scored from AMBER to GREEN on committed evidence without re-running.
Source: [`LEARNING.md` M1](../LEARNING.md), [`ROADMAP.md` M0 correction](../ROADMAP.md).

**Inference** — the "judged once, never re-run" rule (zero M1 cells re-run in M2, M2
comparators never re-touched after escalation) is the corollary of pre-commitment: a
gate that can be re-run until it clears is not a gate. Rests on [`DECISIONS.md`](../DECISIONS.md) D16 ("zero M1 cells
re-run") and [`ROADMAP.md`](../ROADMAP.md) M2 section.

### The hand-read checkpoint as mandatory bug-catch

**Fact** — every milestone included a mandatory N=20 checkpoint with a human hand-read
of ≥3 randomly sampled raw trajectories. This caught two live parser bugs (unit trap
at M0, escaped-dollar at M1) and one model-behavior confound (M4's ordering-correction
interaction) before the full grid ran. Source: [`LEARNING.md`](../LEARNING.md) M0, M1, M4 sections.

**Fact** — the M0 lesson is recorded explicitly in [`LEARNING.md` M0](../LEARNING.md):
"validators prove the machinery can't fool itself; only hand-reading real trajectories
proves the readout is pointed at the right place."

**Fact** — the deterministic fake (anti-rig suite) answers `ANSWER: <drift>` in dollars,
perfectly formatted, on every turn. It validates mechanics but cannot catch format drift
or unit-transform bugs — both of which the hand-reads caught. Source: [`LEARNING.md`](../LEARNING.md) M0,
[`DECISIONS.md`](../DECISIONS.md) D11 outcome.

### The no-peek pledge (enforced in code)

**Fact** — claim 3's counting rule was committed 2026-07-07 while the comparator's
abstain-vs-emit split sat uncounted on disk from M1. `m2.judge` refuses to tally either
arm until the blank cell reaches its final N — a unit test pins this refusal. When the
count ran at judge time, the 52/90 was seen for the first time by any reader. Source:
[`LEARNING.md` M2](../LEARNING.md), [`DECISIONS.md`](../DECISIONS.md) D17.

**Inference** — this is code-level enforcement of a no-peek pledge: the constraint is
stronger than a promise because it cannot be violated by accident.

### What counts as a null

**Decision** — D9, [`DECISIONS.md`](../DECISIONS.md): a disposition probe NULL (gap
straddling zero on the claim-3 disposition check) is a reportable result consistent
with the paper's own predicted abstainer behavior, not an error to hide or extend.
Llama and qwen72b's claim-3 nulls are reported plainly in every milestone table.

**Fact** — the project's headline ("worse than empty") was gated on ≥1 disposed-to-answer
model, not all three. This was written in [`docs/KICKOFF.md`](../docs/KICKOFF.md) before
any paid call, so the deepseek-only CLEARED verdict is an honest result, not retrofitted scope.

## Sources
- [`stats.py`](../stats.py) — Wilson and Newcombe functions, module docstring explaining the choice
- [`DECISIONS.md`](../DECISIONS.md) — D1–D31 ledger; D4, D7, D8, D9, D14, D16, D17, D20, D25, D29 are the core honesty decisions
- [`docs/KICKOFF.md`](../docs/KICKOFF.md) — pre-registered claims, verdict vocabulary, riskiest assumptions
- [`LEARNING.md`](../LEARNING.md) — teaching notes on each milestone's honesty machinery (M0–M5)
- [`ROADMAP.md`](../ROADMAP.md) — evidence of outcomes matching pre-committed rules

## Uncertainties & contradictions

None identified as of this review. The one design reversal (D28-A → D28-B) was executed
before any paid run and is documented in [`DECISIONS.md` D28](../DECISIONS.md) with a
rationale that the replication's job is "reproduce the *published* finding," not a
pre-registered design that turned out to misread the paper's actual design.

## Related pages
- [Results-Synthesis](Results-Synthesis.md)
- [Cross-Check-Against-Author-Code](Cross-Check-Against-Author-Code.md)

## Relevance to current work
This project is CLOSED (D31, 2026-07-09). A future reader would come here to extract
the honesty disciplines for re-use in a successor replication project — specifically the
Wilson/Newcombe gate patterns in `stats.py`, the pre-commitment timeline, and the
mandatory-checkpoint hand-read rule. The `stats.py` module is already noted in project
memory as a reusable pattern.

_Last reviewed: 2026-07-26_
