"""grader.py — ANSWER-line parser + abstain/emit classifier (M0 task 2). Never an LLM judge.

Parsing is where silent scoring corruption lives: the paper's own v2 fixed a parser bug
here. Their old loose fallback grabbed any trailing number, which turned an abstention
like "I can't recompute, though the earlier figure was 55" into a phantom confident-wrong
commit — inflating exactly the blank-vs-lossy emission gap our claim 3 gates on. The
fixed rule, re-typed verbatim from reclaim-eval `src/reclaim/llm.py::parse_answer` (D6):
the number must sit immediately after the LAST 'ANSWER:' marker (allowing markdown/quote
wrapping, a $ sign, and whitespace); no adjacent number means NO numeric commit → None.

Scoring mirrors their `experiment.py::score`: a reply reclaims iff the parsed value is
within TOL of the true answer — regardless of hedging in the surrounding prose ("strict
scoring": the ANSWER line is the commitment).

Abstain-vs-emit mirrors their `probe.py::_is_abstain`: a wrong reply counts as an
ABSTENTION if no value parses OR a hedge phrase (their _HEDGE list, verbatim) appears —
so a hedged reply that still carries an ANSWER value reads as abstaining, exactly as
their pipeline reads it (their DryRun's no-source reply is literally "I am not sure I
have enough to recompute. ANSWER: <v>", classified as abstention). Both raw signals
(`parsed`, `hedged`) are kept on every Grade so this classification choice stays
auditable per trial.

Numeric-only: the logic family's word parser is gated post-v1 (D2) and was not ported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from problems import Problem

# markdown / quote / bracket noise a model may wrap the answer in ("ANSWER: **167**"),
# skipped between the colon and the value so an emphasised commit isn't misread as an
# abstention — verbatim from their llm.py
_WRAP = r"[*_`'\"(\[]*\s*"

# numeric tolerance for "same value" — their score() uses < 0.5 against the true answer;
# we apply the same width when matching the attractor (symmetric treatment, and the
# validator guarantees |drift − correct| ≥ 7, so the two bands can never overlap)
TOL = 0.5

# hedge phrases marking a decline — verbatim from their probe.py _HEDGE
_HEDGE = ("not sure", "cannot", "can't", "can not", "don't have", "do not have",
          "enough to recompute", "unable", "insufficient", "no way to", "need the original")

# trial outcomes
RECLAIMED = "reclaimed"                # committed the TRUE value (the correction landed)
ABSTAIN = "abstain"                    # declined: no parsed value, or hedged
EMIT_ATTRACTOR = "emit_attractor"      # confidently re-emitted the inherited stale value
EMIT_OTHER = "emit_other_wrong"        # confidently emitted some other wrong value
OUTCOMES = (RECLAIMED, ABSTAIN, EMIT_ATTRACTOR, EMIT_OTHER)


def parse_answer(text: str) -> float | None:
    """The number on the last 'ANSWER:' line, required to sit immediately after the
    marker (modulo markdown/$/whitespace). No adjacent number → None, never a number
    scraped out of refusal prose."""
    if not text:
        return None
    m = re.findall(rf"ANSWER\s*:\s*{_WRAP}\$?\s*(-?\d[\d,]*\.?\d*)", text, flags=re.I)
    if not m:
        return None
    try:
        return float(m[-1].replace(",", ""))
    except ValueError:
        return None


def is_hedged(text: str) -> bool:
    """Does the reply carry a decline phrase (their _HEDGE list)?"""
    low = (text or "").lower()
    return any(h in low for h in _HEDGE)


@dataclass(frozen=True)
class Grade:
    parsed: float | None   # the committed value, if any (raw signal, always logged)
    hedged: bool           # hedge phrase present (raw signal, always logged)
    outcome: str           # one of OUTCOMES


def grade(reply: str, problem: Problem) -> Grade:
    """Classify one session-2 reply. Order of tests mirrors their pipeline:
    correct value → RECLAIMED (hedging ignored, per their score()); otherwise
    no value or hedged → ABSTAIN (their _is_abstain); otherwise the emitted wrong
    value is the attractor or some other number."""
    parsed = parse_answer(reply)
    hedged = is_hedged(reply)
    if parsed is not None and abs(parsed - problem.correct) < TOL:
        outcome = RECLAIMED
    elif parsed is None or hedged:
        outcome = ABSTAIN
    elif abs(parsed - problem.drift) < TOL:
        outcome = EMIT_ATTRACTOR
    else:
        outcome = EMIT_OTHER
    return Grade(parsed, hedged, outcome)


def emitted_wrong(g: Grade) -> bool:
    """Claim 3's counting rule: a confident wrong emission (attractor or otherwise)."""
    return g.outcome in (EMIT_ATTRACTOR, EMIT_OTHER)


def took(reply: str, problem: Problem) -> bool:
    """Drift-take test (session 1): did the model COMMIT to the planted wrong total on
    its ANSWER line? Strict value test, no hedge involvement — commitment is the value.
    Every reclaim measurement conditions on this being True (D8's pilot measures it)."""
    parsed = parse_answer(reply)
    return parsed is not None and abs(parsed - problem.drift) < TOL
