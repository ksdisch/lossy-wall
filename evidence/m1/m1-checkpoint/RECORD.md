# M1 checkpoint record — the scheduled N=20 interim look (D14)

Performed 2026-07-06, before any cell extended past 20. Raw per-model outputs (counts,
futility screen, and the seeded 3-trial-per-cell samples read below) are the
`checkpoint-<model>.txt` files beside this record; they are reproducible from the
committed grid rows via `uv run m1.py checkpoint <model>` (rng_seed 0) **at N=20** —
these captures are the record of what was read at the gate.

## Futility screen (≥4 lossy reclaims at 20 → not-cleared, stop)

| model | lossy@0.1 | lossy@0.3 | futile cells |
|---|---|---|---|
| llama | 0/20 | 0/20 | none |
| deepseek | 1/20 | 0/20 | none |
| qwen72b | 0/20 | 0/20 | none |

No cell futile; every cell proceeds to N=40 per the pre-committed schedule.

## Hand-read: 36 sampled trials + 1 targeted read, all verified

**Scoring verified on every sample** — outcome, parsed value, and hedge flag were
checked against the raw note + reply; for every source_first reclaim the arithmetic
in the reply was re-done by hand and matches both the parsed value and the problem.

- **llama (12 samples):** lossy failures are genuine — requests for the missing line
  items, rambling hypothetical arithmetic that never lands (two replies hit the
  600-token cap mid-loop → no ANSWER line → abstain, correctly), one confident
  re-emission of the planted subtotal correctly classed `emit_other_wrong`, one
  hedged attractor re-emission correctly classed abstain (per the paper's
  `_is_abstain`: hedge + value = abstention). All 6 sf samples recompute from the
  facts (e.g. 9×$6+3×$5=$69) — genuine reclaims.
- **deepseek (12 samples + the stray):** same phenomenology; one live confirmation
  the PR #10 parser fix matters in session 2 (`ANSWER: \$59` now parses, classed
  hedged abstain). One pure confabulation ("let's assume the correct subtotal is
  $200") classed `emit_other_wrong`. **The single lossy@0.1 reclaim was read
  individually:** the model *assumed* a round-number subtotal with no source in
  context and landed on the true total by luck ($150 vs attractor $157) — the
  paper's DryRun "lucky recovery" case. Under strict scoring it stays a reclaim
  (commitment is the value; unscoring by process would bend the gate); the D14
  ladder exists precisely for this — the cell escalates at 40 rather than being
  hand-waved either way.
- **qwen72b (12 samples):** all lossy samples are hedged hypotheticals ("let's
  assume the plates were $13...") ending in assumed values or explicit requests for
  the missing details — every one correctly abstain; both `parsed`-carrying abstains
  are hedged, so the classifier read them exactly as the paper's pipeline would.
  All 6 sf samples recompute genuinely (14×12+2×10=188; 15×9+11×10=245; etc.).

## The advisory source_first eye (the brief's explicit worry)

M0 never ran source_first; the paper reports RR 0.99–1.00. Ours reads **20/20 in all
six sf cells at the checkpoint** with hand-verified recomputation behind each sampled
reclaim — no protocol-fidelity concern. The sf@0.1 ≡ sf@0.3 replicate pairs agree
exactly (identical note strings by the g-threshold mapping, as designed).

**Checkpoint verdict: PASS for all three models — extend to N=40.**
