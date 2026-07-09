# M5 paper-boundary extraction (rider a) + mechanism-provenance note (rider b)

*Extracted 2026-07-09 from the author's `reclaim-eval` clone (D1: reference/oracle only,
never imported). This is M5's anchor record. Its first job (M5-BRIEF D30 rider a) was to
establish **how thin the boundary anchor is** — and it materially revises the brief's
"thin anchor" assumption: the anchor is **concrete, not thin.***

## Headline correction to the M5 brief

The M5 brief (written before this extraction) assumed the paper's boundary section was
qualitative and that the released harness had **no** source-size sweep. **Both are wrong.**
The clone ships a full source-size sweep — `scripts/bench_sizesweep.py`,
`scripts/analyze_sizesweep.py`, and `src/reclaim/sizesweep.py` — with concrete anchor
numbers, a released fake, and a mechanism analysis. This changes two things:

1. **The anchor is concrete** (numbers below), so D29 can compare direction *and* the
   crossover *trend* descriptively, not just "is there a cliff."
2. **The paper's actual sweep axis is D28-B, not the signed D28-A.** The paper **fixes the
   character budget and grows the source size N**, at **two budgets**, to disentangle
   budget-starvation from problem-difficulty — the exact confound D28-A was chosen to
   avoid. The paper answers that confound with its two-budget design instead. This is a
   readout-design divergence from the signed decision and is surfaced to Kyle before any
   paid run (see "Divergence from the signed D28" below).

## The paper's boundary claim, verbatim (README `### The boundary, and how the fix fails`)

> `source_first` is not unconditional; two sweeps map its edge, and both are
> capability-invariant:
>
> - **Size.** Grow the source past the budget and it cannot all be kept; reclaim cliffs to
>   0.00 the instant one item is dropped. The cliff tracks the *budget*, not problem size
>   (N≈5 at B=300, N≈14 at B=600). `bench_sizesweep.py`.
> - **Noise.** Bury the few answer-determining items among plausible decoys and a positional
>   note lets them get crowded out; reclaim decays to the lossy floor while a relevance-aware
>   note holds flat. `bench_noisysweep.py`.
> - **Silent failure, and the fix for it.** Past its boundary `source_first` does not
>   abstain; it confidently sums the *partial* source (Opus: 96/96 silent mis-sums). A
>   one-line **completeness tag** (k of N items preserved) flips that to 94/96
>   flagged-or-abstained. … A **write-time recompute certificate** … splits reclaim 0.93
>   (pass) vs 0.00 (flag) *capability-free* … (`bench_completeness.py`,
>   `analyze_certificate.py`).

**M5 scope is the Size bullet only.** Noise (`bench_noisysweep.py`) and the silent-failure
fixes (completeness tag, recompute certificate) are separate arms, explicitly NOT in M5.

## The anchor numbers (the comparison target — direction + structure, never point-matched)

| quantity | paper value | source |
|---|---|---|
| crossover N (source_first still > 0.5) at budget **B=300** | **N ≈ 5** | README Size bullet |
| crossover N at budget **B=600** | **N ≈ 14** | README Size bullet |
| cliff sharpness | "cliffs to **0.00 the instant one item is dropped**" | README Size bullet |
| failure mode past the cliff | **silent mis-sum** — source_first confidently sums the *partial* source (does NOT abstain) | README Silent-failure bullet |
| the mechanism variable | whether the **full** source survived the budget (`k_items == N`) | `analyze_sizesweep.py::mechanism` |

The central structural claim — **"the cliff tracks the budget, not problem size"** — is
proven by the two budgets giving *different* crossover N (5 vs 14). If the cliff were
problem-difficulty, the crossover would sit at the same N regardless of budget.

## The paper's released design (`bench_sizesweep.py`)

- **Axis:** fix the carried-memory **character budget B**, sweep the ledger **size N** (line
  items). Docstring: *"As N outgrows B, the source-first note can keep only k<N items and an
  exact sum needs all N, so its reclaim advantage decays to the lossy floor. Two budgets show
  the crossover moves with B."*
- **Grid:** `N_STORES = 8` stores × `Ns = [2,3,4,5,6,8,10,12,14,16,20,24,32]` ×
  `budgets = [300, 600]` × `policies = (source_first, lossy_padded)` × `seeds = 3`, directed
  arm, **temperature 0.7** (the paper-caption temp, not the tool's 0.0 default — the M3
  labeling nuance recurs).
- **Floor comparator:** `lossy_padded` (budget-matched), **not** bare lossy — the padded
  note is the same length as source_first, so the cliff can't be "it had less text."
- **`build_note(led, b, pol)`** returns `(note, k, locus_kept)` — `k` = how many whole line
  items the budget kept. `k < N` is the cliff regime.
- **`SizeFake`** (their released validator), verbatim behaviour:
  > recomputes the correct total **IFF** the carried note contains **every** line-item clause
  > (the full source). It therefore reclaims only when the budget kept all N items; past the
  > cliff (k<N) it returns the **inherited wrong total**. A real model scoring above this past
  > the cliff is confabulating, not recomputing.
- No sizesweep data is committed in the clone (`data/results/` ships empty — the same
  reproduce-from-artifacts gap M0/M3 recorded).

## Mechanism-provenance note (rider b): ours vs theirs

Our free build (this session) is **faithful to the paper's core mechanism**, built
independently (D6: reference, re-type, never import):

| our construction | their mechanism | match |
|---|---|---|
| `fake.SourceSizeFake` — reclaims only when **all** line-item clauses are present | `bench_sizesweep.SizeFake` — same all-clauses test | **identical in spirit**; one difference below |
| `notes.retained_fraction` (graded per-trial gate) | `analyze_sizesweep.mechanism` split on `k_items == N` | same variable (full vs partial source) |
| `notes.memory_note_sized` — budget-capped source_first keeps whole items | `sizesweep.build_note` — budget-capped note, returns `k` kept | same operation |
| `problems.generate_sized` — K-item receipt | `sizesweep.make_ledger(store, N)` | same (N-item ledger) |

**One faithful upgrade to fold in:** their `SizeFake` returns the **drift (inherited wrong
total)** past the cliff, not a hedge — modelling the paper's *silent mis-sum* failure mode.
Our `SourceSizeFake` currently returns the hedged no-source reply past the cliff (inherited
from `DriftFake`), which our arithmetic grader reads as ABSTAIN. To report the paper's
silent-failure story (source_first EMITs the drift past the cliff, worse-than-empty), the M5
readout should classify the past-cliff outcome (EMIT_ATTRACTOR vs ABSTAIN) — our `grader`
already does this; only the fake's past-cliff reply should switch from hedge to drift-commit
to validate that path. (Small, noted for the build.)

## Divergence from the signed D28 (surfaced to Kyle — no paid run until resolved)

- **Signed (D28-A):** fix the receipt at K=6, sweep the note budget, report source_first
  reclaim vs retained-source fraction s at **one** problem size. Chosen to avoid the
  problem-difficulty confound.
- **Paper (D28-B):** fix the budget, grow N, at **two** budgets — the confound is answered by
  showing the crossover **tracks the budget** (N≈5@300 vs N≈14@600), plus the full-vs-partial
  mechanism split.
- **Consequence:** D28-A cannot reproduce the paper's central claim ("the cliff tracks the
  budget, not problem size") — that needs ≥2 budgets on the N axis. The recommendation to
  Kyle is to **reopen D28 and adopt the paper's design** (grow N at B∈{300,600},
  source_first vs lossy_padded, crossover per budget, mechanism split). The free-build
  foundation (generator, budget-capped note, graded gate, the all-clauses fake, the cliff
  gate) transfers to that design with modest additions.

## What this does to D29's gate

The concrete anchor lets D29 keep its existence+direction gate **and** add a descriptive
structural check the brief couldn't: **the crossover N is larger at the larger budget**
(the "tracks the budget" claim). Still no point-matching (N≈5 / N≈14 are direction anchors,
not targets), and still no DISCREPANT unless an oracle overlap cell is added — but the anchor
is firm enough that a NULL here would be genuinely surprising, and a REPRODUCED sits beside
real paper numbers.
