# M3 paper-number extraction — arXiv 2606.25449 v2 (fetched 2026-07-07)

The free extraction task from `docs/M3-BRIEF.md`: pin the paper-committed numbers the
comparison table cites, verbatim, with sources. Fetched from the arXiv v2 HTML
(`https://arxiv.org/html/2606.25449v2`) in two independent passes (a broad pass and a
verbatim character-by-character pass); the passes agree on every cell reported below.

## tab:wall — llama-3.1-8b · arithmetic · directed RR (95% bootstrap CI)

As printed in the paper's Table 5, llama rows, all four integrities:

| g | lossy | lossy_padded | source_first |
|---|---|---|---|
| 1.0 | 0.61 [.52, .71] | 0.85 [.78, .92] | 0.61 [.52, .71] |
| 0.6 | 0.82 [.74, .90] | 0.85 [.78, .92] | 0.70 [.60, .78] |
| 0.3 | 0.01 [0, .03] | 0.00 [0, 0] | 0.99 [.97, 1] |
| 0.1 | 0.00 [0, 0] | 0.00 [0, 0] | 0.99 [.97, 1] |

Caption, verbatim: *"Arithmetic: the wall (lossy), the length control (lossy-padded),
and the fix (source-first), two models. Directed RR (95% CI) vs. memory integrity g
(llama n=96; grok n=24; temperature 0.7)."*

Methods sentence, verbatim: *"Every condition is run over three seeds at temperature
0.7 (the Claude models in the replay run at their default, as Opus does not accept the
parameter)."*

CI method: table captions say "95% bootstrap CI"; the paper does not state the
resample count in the fetched content. The released harness's `boot_ci` (identical in
`scripts/analyze_realworld.py` and `scripts/integrity_table_ci.py`) uses B=5,000,
seed 0, percentile read — the method `bootstrap.py` re-types.

## The sampling-config finding (labels the comparison table's temperature column)

The paper's tab:wall is **temperature 0.7** (caption + methods, verbatim above). The
released tool's default — `run_pilot.py --temp` — is **0.0**, which equals our D10
sampling. So: ours (0.0) and the oracle run (0.0) are sampling-matched by
construction; the paper-committed column is 0.7 and is labeled as such. Direction +
structure is the comparison's job (KICKOFF non-goal: no point-matching), and D19
rider (a) — a 0.7 repeat — was declined at sign-off.

## The artifact-vs-paper variance (footnoted under the comparison table)

The repo README's "Findings" wall table (their artifact, current clone) prints the
llama arithmetic row as lossy 0.00/0.00 · padded 0.00/0.00 · source_first
**0.96/1.00** at g=0.3/0.1 — while the paper v2 prints lossy **0.01**/0.00 and
source_first **0.99/0.99**. Same experiment, same n, last-digit disagreement on three
cells. Both are the author's numbers; the comparison table's "paper-committed" column
carries the **paper's** values (the pre-registered comparison target), and this
variance is recorded as a footnote. No gate touches it (the agreement criterion
judges their-run vs ours, not the paper column).

## tab:blank / disposition (claim 3's comparison targets, post-v2 corrected)

- Paper tab:blank (broad pass): llama lossy-emit **0.17**, n=96. Matches
  `NOTE_parser_fix.md` ("tab:blank lossy emit (llama / grok): … corrected 0.17 / 0.57").
- Disposition deltas (post-v2 corrected values; source `NOTE_parser_fix.md`, the
  author's correction of record, confirmed against the paper's corrected framing):
  deepseek-chat **+0.83**, grok **+0.57**, qwen-2.5-7b **+0.39**, llama-3.1-8b
  **+0.17**; the four frontier OpenAI/Anthropic models **0.00** (abstainers).
  n=96/cell, g=0.1, directed.

## Where each number lands

- `m3.PAPER["wall_llama"]` — the paper table above, points + brackets (pinned by
  `test_m3.py::test_paper_constants_match_their_published_findings`).
- `m3.PAPER["wall_temp"]` = 0.7 — the temperature column's paper label.
- `m3.PAPER["readme_wall_llama"]` — the README variant, kept for the footnote.
- `m3.PAPER["disposition_delta"]`, `m3.PAPER["blank_lossy_emit_llama"]` — claim-3 rows.
