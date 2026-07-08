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

The logic family's closed-option word parser was ported when M4 opened (2026-07-08);
see the text-family section at the foot of this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from problems import Problem

# markdown / quote / bracket noise a model may wrap the answer in ("ANSWER: **167**"),
# skipped between the colon and the value so an emphasised commit isn't misread as an
# abstention — verbatim from their llm.py
_WRAP = r"[*_`'\"(\[]*\s*"

# our one widening beyond their verbatim wrap set (found live 2026-07-06 by the M1
# bank hand-read): deepseek LaTeX-escapes the currency symbol — 'ANSWER: \$197' — on
# about a third of its replies. That is a numeric commit any human reads as $197;
# refusing it scored true takes as no-takes (M0's deepseek pilot read 13/20 when the
# raw replies show 20/20) and would have graded session-2 reclaims as abstentions.
# The escape is accepted ONLY immediately before the $ — refusal prose still parses
# to None, so the paper's v2 bug cannot return through this door.
_DOLLAR = r"\\?\$?"

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
    m = re.findall(rf"ANSWER\s*:\s*{_WRAP}{_DOLLAR}\s*(-?\d[\d,]*\.?\d*)", text, flags=re.I)
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


# ── the logic (text) family: closed-option single-token readout + failure taxonomy ─────────
# M4 (opened 2026-07-08). Re-typed from reclaim-eval llm.py::parse_answer_word,
# experiment.py::score/_logged_answer, and scripts/logic_failmode.py::classify (D6: reference,
# re-type, never import). The symbolic answer space is CLOSED — every valid answer is one of
# the problem's own candidate tokens — so a word off that set reads as an ABSTENTION, never a
# phantom commit (the word-answer analogue of parse_answer's v2 fix). reclaim == recov; the
# D25 gap gates on it.

# fallback filler/refusal blocklist for text problems with NO declared options — verbatim from
# their llm.py _NONANSWER. Our logic problems all carry options, so this is only the unused
# fallback path, re-typed for a faithful port.
_NONANSWER = frozenset({
    "please", "unable", "cannot", "cant", "none", "nobody", "noone", "unknown", "unclear",
    "insufficient", "sorry", "i", "no", "not", "na", "n", "without", "need", "more",
    "there", "the", "a", "an", "sufficient", "determine", "provide", "details", "detail",
    "information", "info", "memory", "context", "unsure", "unspecified", "undetermined",
    "indeterminate", "ambiguous", "uncertain", "missing", "lacking", "given", "based",
})

# logic taxonomy buckets (their logic_failmode.py names)
RECOV = "recov"        # committed the CORRECT token — reclaim, on the logic family
INHERIT = "inherit"    # committed the planted DRIFT token — the worse-than-empty signal
NOVEL = "novel"        # committed a different valid option (neither correct nor drift)
ABST = "abst"          # no committed token (an off-set word, or none at all)
LOGIC_BUCKETS = (RECOV, INHERIT, NOVEL, ABST)


def parse_answer_word(text: str, options=None) -> str | None:
    """The single-token answer on the last 'ANSWER:' line. Closed answer space: with
    `options` given, accept the parsed token only if it is one of them (returning the
    canonical-cased option) and treat anything else as an abstention — a real validator
    against the known answer set, not a guess at what filler looks like. Verbatim from their
    llm.py::parse_answer_word; the blocklist path is only a fallback for problems with no
    declared options."""
    if not text:
        return None
    m = re.findall(rf"ANSWER\s*:\s*{_WRAP}([A-Za-z][A-Za-z/]*)", text, flags=re.I)
    if not m:
        return None
    w = m[-1]
    if options:
        for o in options:
            if w.lower() == str(o).lower():
                return o            # commit only to a recognised candidate
        return None                 # an unrecognised word == abstention, never a phantom commit
    return None if w.lower() in _NONANSWER else w


def score_text(reply: str, problem: Problem) -> bool:
    """recov test (their experiment.py::score, text branch): the committed token equals the
    correct single-word answer, case-insensitively. This is reclaim, on the logic family."""
    tok = parse_answer_word(reply, getattr(problem, "options", None))
    return tok is not None and str(tok).lower() == str(problem.correct).lower()


def classify_logic(reply: str, problem: Problem) -> str:
    """The four-way logic readout (their logic_failmode.py::classify): RECOV (correct) /
    INHERIT (the planted drift token — worse than empty) / NOVEL (another valid option) /
    ABST (no committed token). reclaim == (classify_logic(...) == RECOV) by construction."""
    if score_text(reply, problem):
        return RECOV
    tok = parse_answer_word(reply, getattr(problem, "options", None))
    if tok is None:
        return ABST
    if str(tok).strip().lower() == str(problem.drift).strip().lower():
        return INHERIT
    return NOVEL


def took_logic(reply: str, problem: Problem) -> bool:
    """Drift-take test (session 1, logic): did the model COMMIT the planted drift token on
    its ANSWER line? The take that every logic reclaim measurement conditions on (D24's
    pilot measures it) — the text sibling of took()."""
    tok = parse_answer_word(reply, getattr(problem, "options", None))
    return tok is not None and str(tok).strip().lower() == str(problem.drift).strip().lower()
