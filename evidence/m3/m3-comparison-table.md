## The comparison table — llama · arithmetic · directed

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
