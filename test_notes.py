"""test_notes.py — the note policies' g-threshold behavior and the per-trial source gate.
No network, no model.

This file is the write-time half of the experiment's integrity: for every policy × g cell
we assert exactly which ingredients (source facts / planted premise / stale conclusion)
the note carries. If a template drifts, the cell definitions drift, and these fail.
"""
from __future__ import annotations

import pytest

from notes import (INTEGRITY, PAD, POLICIES, SRC_MARKER, _concl, conclusion_present,
                   memory_note, source_present)
from problems import CANONICAL

P = CANONICAL[0]                      # notebooks: correct 46, drift 55
CONCL = "$55"                         # how the templates format the carried conclusion


def test_concl_formatting():
    assert _concl(P) == CONCL         # drift (the committed WRONG value), not correct


def test_lossy_thresholds():
    # g >= 0.5: facts + premise + conclusion all present
    for g in (1.0, 0.6):
        note = memory_note(P, g, "lossy")
        assert source_present(note, P)
        assert P.wrong_premise in note
        assert conclusion_present(note, P)
    # the wall opens: 0.2 <= g < 0.5 keeps premise + conclusion, sheds the source
    note = memory_note(P, 0.3, "lossy")
    assert not source_present(note, P)
    assert P.wrong_premise in note
    assert conclusion_present(note, P)
    # g < 0.2: conclusion only
    note = memory_note(P, 0.1, "lossy")
    assert not source_present(note, P)
    assert P.wrong_premise not in note
    assert conclusion_present(note, P)


def test_source_first_thresholds():
    # source_first keeps the source at EVERY g — that's the policy
    for g in INTEGRITY:
        assert source_present(memory_note(P, g, "source_first"), P)
    # conclusion carried at g >= 0.5, dropped below (re-derivable, so it goes first)
    for g in (1.0, 0.6):
        assert conclusion_present(memory_note(P, g, "source_first"), P)
    for g in (0.3, 0.1):
        note = memory_note(P, g, "source_first")
        assert not conclusion_present(note, P)
        assert "the earlier answer may be off" in note


def test_lossy_padded_budget_match():
    for g in INTEGRITY:
        lossy = memory_note(P, g, "lossy")
        sf = memory_note(P, g, "source_first")
        padded = memory_note(P, g, "lossy_padded")
        # identical content to lossy, extended with PAD repeats to >= source_first's length
        assert padded.startswith(lossy)
        assert len(padded) >= len(sf)
        suffix = padded[len(lossy):]
        assert suffix == PAD * (len(suffix) // len(PAD)) if suffix else True
    # at the wall the padding must NOT smuggle the source back in
    assert not source_present(memory_note(P, 0.1, "lossy_padded"), P)
    assert conclusion_present(memory_note(P, 0.1, "lossy_padded"), P)


def test_blank_carries_nothing():
    for g in INTEGRITY:
        note = memory_note(P, g, "blank")
        assert not source_present(note, P)
        assert not conclusion_present(note, P)
        assert P.wrong_premise not in note
        assert P.ask in note          # only that an earlier session was determining `ask`


def test_unknown_policy_raises():
    # their code silently fell through to lossy on a typo; ours must crash instead
    with pytest.raises(ValueError):
        memory_note(P, 0.1, "sourcefirst")


def test_wall_cell_definitions_all_policies():
    # the disposition probe's exact cells (g=0.1): lossy carries the stale value with no
    # source (silent regime); blank carries neither (loud regime)
    lossy = memory_note(P, 0.1, "lossy")
    blank = memory_note(P, 0.1, "blank")
    assert conclusion_present(lossy, P) and not source_present(lossy, P)
    assert not conclusion_present(blank, P) and not source_present(blank, P)


def test_source_marker_mechanics():
    # the gate keys on the first SRC_MARKER chars of the facts string, case-insensitive
    marker = P.facts[:SRC_MARKER]
    assert source_present(f"...{marker.upper()}...", P)
    assert not source_present("no ledger details here", P)
    assert not source_present("", P)
    assert len(POLICIES) == 4
