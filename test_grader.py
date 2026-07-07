"""test_grader.py — the parser and classifier, pinned to the cases that matter.
No network, no model.

The first test IS the paper's v2 parser bug: an abstention whose prose mentions the old
figure must parse to None, never to a phantom commit. If that regression ever returns,
claim 3's emission gap inflates silently — this file is where it gets caught instead.
"""
from __future__ import annotations

from grader import (ABSTAIN, EMIT_ATTRACTOR, EMIT_OTHER, RECLAIMED, emitted_wrong,
                    grade, is_hedged, parse_answer, took)
from problems import CANONICAL

P = CANONICAL[0]   # notebooks: correct 46, drift 55


def test_parser_bug_case_from_the_paper():
    # the v2 fix: no number adjacent to ANSWER: -> None, even if prose carries a figure
    assert parse_answer("I can't recompute, though the earlier figure was 55") is None
    assert parse_answer("Without the line items I cannot verify the total of 55.") is None


def test_parser_accepts_wrapped_commits():
    assert parse_answer("ANSWER: 55") == 55.0
    assert parse_answer("ANSWER: **167**") == 167.0
    assert parse_answer("ANSWER: $ 1,234.50") == 1234.5
    assert parse_answer("answer: 46") == 46.0            # case-insensitive marker
    assert parse_answer("ANSWER: `-7`") == -7.0
    assert parse_answer("ANSWER: '46'") == 46.0


def test_parser_accepts_latex_escaped_dollar():
    # found live on deepseek, 2026-07-06, by the M1 bank hand-read: it emits the
    # dollar sign LaTeX-escaped ('ANSWER: \$197') on a third of its take replies.
    # That is a numeric commit any human reads as $197 — refusing it under-counted
    # deepseek's M0 take 13/20 when the truth was 20/20 (all seven misses were this
    # shape, all committing the drift). The exact live shapes, pinned:
    assert parse_answer(r"ANSWER: \$197") == 197.0
    assert parse_answer(r"ANSWER: \$86**  ") == 86.0     # escaped AND trailing markdown
    assert parse_answer(r"ANSWER: \$1,234.50") == 1234.5
    # the escape alone is not a commit
    assert parse_answer(r"ANSWER: \$") is None


def test_took_and_grade_survive_the_escaped_dollar():
    # the load-bearing halves: take-conditioning (bank) and session-2 scoring (grid) —
    # an escaped reclaim must never grade as an abstention (it would deflate
    # source_first RR, exactly claim 1's denominator)
    assert took(rf"ANSWER: \${P.drift:g}", P) is True
    g = grade(rf"Rechecking the items... ANSWER: \${P.correct:g}", P)
    assert g.outcome == RECLAIMED and g.parsed == P.correct
    g = grade(rf"ANSWER: \${P.drift:g}", P)
    assert g.outcome == EMIT_ATTRACTOR


def test_parser_takes_last_answer_line():
    reply = "ANSWER: 55\nWait, rechecking the items... ANSWER: 46"
    assert parse_answer(reply) == 46.0


def test_parser_rejects_non_numeric_and_empty():
    assert parse_answer("ANSWER: unknown") is None
    assert parse_answer("ANSWER:") is None
    assert parse_answer("") is None
    assert parse_answer(None) is None


def test_hedge_detection():
    assert is_hedged("I am not sure I have enough to recompute. ANSWER: 55")
    assert is_hedged("There is no way to rebuild the subtotal.")
    assert not is_hedged("Rechecking... ANSWER: 46")


def test_grade_reclaimed_ignores_hedging():
    # their score(): the ANSWER line is the commitment; prose hedging doesn't undo a
    # correct value
    g = grade("I'm not sure, but recomputing: ANSWER: 46", P)
    assert g.outcome == RECLAIMED and g.hedged is True
    g = grade("Rechecking... ANSWER: 46.4", P)            # inside the 0.5 tolerance
    assert g.outcome == RECLAIMED


def test_grade_abstains():
    # no value at all
    g = grade("I cannot determine this without the original line items.", P)
    assert g.outcome == ABSTAIN and g.parsed is None
    # their _is_abstain: hedge + a wrong value still reads as an abstention — the
    # DryRun's no-source reply is exactly this shape
    g = grade("I am not sure I have enough to recompute. ANSWER: 55", P)
    assert g.outcome == ABSTAIN and g.parsed == 55.0 and g.hedged is True
    assert not emitted_wrong(g)


def test_grade_emissions():
    g = grade("Using the note from last time: ANSWER: 55", P)
    assert g.outcome == EMIT_ATTRACTOR and emitted_wrong(g)
    g = grade("It should be ANSWER: 60", P)
    assert g.outcome == EMIT_OTHER and emitted_wrong(g)
    g = grade("Recomputed. ANSWER: 46.6", P)              # outside tolerance of 46
    assert g.outcome == EMIT_OTHER


def test_take_classification():
    # session-1 commitment to the planted wrong total: value test, hedging irrelevant
    assert took("Using what was given, ANSWER: 55", P) is True
    assert took("ANSWER: 46", P) is False                 # answered correctly = no take
    assert took("The pens are an issue here.", P) is False
