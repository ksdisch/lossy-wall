# M2 checkpoint record — the scheduled N=20 interim look (D16/D17/D18)

Performed 2026-07-07, per model, before any of that model's cells extended past 20.
Raw per-model outputs (counts and the seeded 3-trial-per-cell samples read below) are
the `checkpoint-<model>.txt` files beside this record; they are reproducible from the
committed grid rows via `uv run m2.py checkpoint <model>` (rng_seed 0) **at N=20** —
these captures are the record of what was read at the gate. No futility screen exists
for M2 cells (D16: the containment boundary is comparator-dependent, so the
checkpoint's only power here is the hand-read). Nothing can clear at 20.

## Counts at the gate (reclaims / trials)

| model | padded@0.1 | padded@0.3 | lossy@0.6 | lossy@1.0 | sf@0.6 | sf@1.0 | blank |
|---|---|---|---|---|---|---|---|
| deepseek | 1/20 | 0/20 | 20/20 | 20/20 | 20/20 | 20/20 | 0/20 |
| qwen72b | 0/20 | 1/20 | 20/20 | 20/20 | 20/20 | 20/20 | — |
| llama | 0/20 | 0/20 | 18/20 | 16/20 | 14/20 | 12/20 | — |

## The M2-specific eyes (the brief's list), what was verified

**Padded notes as sent — the first padded notes ever to run paid.** Mechanical check
over every logged padded row (not just samples): the PAD filler sentence present, the
source demonstrably absent (the 18-char token test), and length ≥ the source_first
note at that g — all three properties held on every row, both models. The per-trial
gate (`verify_note_gate`) had already enforced source-absence before each call spent
a token; the hand-read confirmed the notes read as designed: lossy content + explicit
content-free filler.

**Transcript cells' assembled context.** All sampled lossy@1.0 trials carry the full
19-turn session-1 conversation (system, plant, 8 commitment follow-ups with the
model's replies) with the directed correction appended at run time — the genuine
drift trajectories from the bank, wrong totals visibly committed and restated across
turns. Every sampled transcript reclaim recomputes correctly once the correction
lands (arithmetic redone by hand: deepseek 94/188/93; qwen72b 210/75/66) — the
figure's "nothing was compressed" left anchor behaves as the paper says it should.

**Blank replies' abstain classification (claim 3 lives here).** deepseek blank@0.1 is
0/20 reclaimed with **all 20 outcomes abstain** at the gate; the three sampled
replies were read word-by-word: each explicitly declines ("Since no figures or
details from the earlier session were retained, I cannot…"), none carries a parsable
ANSWER value, all are hedged — the mechanical classifier reads them exactly as a
human does. The archived lossy@0.1 comparator's split remains **untallied** (the
no-peek pledge holds; `m2.judge` refuses to count it until blank reaches final N).

## Individual reads of the stray padded reclaims (M1's precedent)

- **deepseek padded@0.1, bank trial 18 (1/20):** the model assumes "the correct tags
  subtotal is $150" with no source in context and lands on the true total by luck
  ($150 vs attractor $157) — the same lucky-recovery phenomenology, on the same bank
  trial, as M1's single deepseek lossy@0.1 stray (same trajectory family, nearly
  identical context at temperature 0.0). Under strict scoring it stays a reclaim;
  the D16 ladder judges the cell at 40 against the archived 1/90 comparator.
- **qwen72b padded@0.3, bank trial 4 (1/20):** the model back-derives "other items =
  $27" from the note's own numbers ($81 − $54), then assumes a "placeholder" wrenches
  cost of $45 — which happens to be the true subtotal (the plant is a $9 corruption)
  — and commits the true total $72 while hedging. Correct value on the ANSWER line =
  reclaim (their score(), hedging ignored). If it is still the lone stray at 40, the
  cell escalates and qwen72b's bank top-up contingency fires as priced in the brief.

## Classifier edge-reads worth recording (both signals logged per row)

- Hedged replies that still re-assert the attractor value (e.g. deepseek padded@0.3
  trials 10/13; qwen72b padded@0.1 all three samples) classify as **abstain** under
  the author's verbatim rule (hedge + value = abstention). This errs conservative
  for the claims: it undercounts lossy-side wrong emissions.
- qwen72b padded@0.3 trial 18 invents a tags subtotal ("assume $70") and commits
  $160 with no hedge-list phrase → **emit_other_wrong**, read as a human would.

## llama's knob dip — targeted read of every failure class (the +1 targeted read)

llama's knob cells sit BELOW the ceiling at the gate (lossy@0.6 18/20, lossy@1.0
16/20, sf@0.6 14/20, sf@1.0 12/20) while deepseek and qwen72b sit at 20/20 — the one
anomaly at this checkpoint, so its failing replies were read directly (not just the
seeded samples; all failure classes covered):

- **Token-cap abstains (the majority):** llama rambles into verification loops
  ("However, this is not… Let's recheck…" repeated) and hits the 600-token cap
  (D10, the author's own setting) before ever emitting an ANSWER line → abstain
  under the strict readout. Several such replies contain the CORRECT total mid-ramble
  (e.g. 72+40=112 computed, never committed). Correctly scored: the ANSWER line is
  the commitment. Same llama trait M1's record documented.
- **Genuine attractor re-emissions:** with the source in context (sf@0.6 note, or the
  full transcript), llama computes the correct subtotal, then argues itself back to
  the carried total and commits it ("The correct total before tax is indeed $59" —
  after deriving $66 from the facts). Correctly `emit_attractor` — a real,
  interesting llama correction failure, not a scoring artifact.

Verdict on the anomaly: the dip is REAL measured behaviour (llama's weak
correction-following plus its format fragility at the cap), faithfully read by the
pre-committed readout. These are descriptive cells (they gate nothing); the llama
panel of the knob figure carries this caveat in the M2 notes.

## Verdict

**deepseek: PASS** — extended to N=40 (bank holds 90; the padded@0.1 escalation the
ladder later ordered needs no top-up).
**qwen72b: PASS** — extended toward N=40 in bounded batches (DeepInfra throttle
discipline; one 429 crash between batches, resumed without duplicates).
**llama: PASS** — extended to N=40 after the targeted read above.
