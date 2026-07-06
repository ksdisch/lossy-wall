"""test_runner.py — frame assembly and the per-trial source gate. No network, no model.

The frames are protocol: if a message's role, order, or wording drifts, we're no longer
running the paper's experiment. The gate tests include the adversarial case — a note
smuggled in under the wrong label must CRASH the trial, not run it.
"""
from __future__ import annotations

import pytest

from fake import DriftFake
from notes import INTEGRITY, memory_note
from problems import CANONICAL, FOLLOWUPS
from runner import (ARMS, DEPTH, SYSTEM, SourceGateError, build_trajectory,
                    expected_source_presence, last_answer, plant, reclaim_cross,
                    run_session2, session2_base, verify_note_gate)

P = CANONICAL[0]   # notebooks


def test_plant_wording():
    msg = plant(P)
    assert msg.startswith(P.question)
    assert f"\nNote: {P.wrong_premise}. Use that and give {P.ask}." in msg


def test_correction_wording_both_arms():
    directed = reclaim_cross(P, "directed")
    assert f"I think {P.locus} was wrong" in directed
    assert "'ANSWER: <answer>'" in directed
    generic = reclaim_cross(P, "generic")
    assert "I think there is a mistake" in generic
    assert P.locus not in generic          # generic must NOT name the locus
    with pytest.raises(ValueError):
        reclaim_cross(P, "encoded")
    assert ARMS == ("directed", "generic")


def test_build_trajectory_shape():
    traj = build_trajectory(DriftFake(P), P)
    # [system, user(plant), assistant] + (user, assistant) per follow-up
    assert len(traj) == 3 + 2 * DEPTH
    assert traj[0] == {"role": "system", "content": SYSTEM}
    assert traj[1]["role"] == "user" and traj[1]["content"] == plant(P)
    roles = [m["role"] for m in traj[2:]]
    assert roles == ["assistant"] + ["user", "assistant"] * DEPTH
    assert [m["content"] for m in traj if m["role"] == "user"][1:] == list(FOLLOWUPS[:DEPTH])
    assert last_answer(traj) == traj[-1]["content"]


def test_build_trajectory_depth_bounds():
    assert len(build_trajectory(DriftFake(P), P, depth=0)) == 3
    with pytest.raises(ValueError):
        build_trajectory(DriftFake(P), P, depth=len(FOLLOWUPS) + 1)


def test_session2_note_cells_frame():
    base = session2_base(P, "source_first", 0.1)
    assert base == [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": memory_note(P, 0.1, "source_first")}]
    # the correction is appended as the final user turn
    reply = run_session2(DriftFake(P, seed=1), P, "source_first", 0.1, arm="directed")
    assert isinstance(reply, str) and "ANSWER:" in reply


def test_transcript_special_case_is_lossy_only():
    traj = build_trajectory(DriftFake(P), P)
    base = session2_base(P, "lossy", 1.0, transcript=traj)
    assert base == traj and base is not traj      # same content, defensive copy
    with pytest.raises(ValueError):
        session2_base(P, "lossy", 1.0)            # transcript required
    # every other policy stays note-based at g=1.0
    for policy in ("source_first", "lossy_padded", "blank"):
        base = session2_base(P, policy, 1.0, transcript=traj)
        assert base[1]["content"] == memory_note(P, 1.0, policy)


def test_transcript_gate_requires_the_question():
    bogus = [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": "an unrelated conversation"}]
    with pytest.raises(SourceGateError):
        session2_base(P, "lossy", 1.0, transcript=bogus)


def test_gate_passes_all_legitimate_cells():
    for policy in ("lossy", "lossy_padded", "source_first", "blank"):
        for g in INTEGRITY:
            note = memory_note(P, g, policy)
            verify_note_gate(note, P, policy, g)   # must not raise


def test_gate_catches_a_rigged_note():
    # a note that claims to be a wall-tight lossy note but carries the source: refuse
    smuggled = memory_note(P, 0.1, "source_first")
    with pytest.raises(SourceGateError):
        verify_note_gate(smuggled, P, "lossy", 0.1)
    # and the reverse: a "source_first" cell whose note lost the source
    empty = memory_note(P, 0.1, "blank")
    with pytest.raises(SourceGateError):
        verify_note_gate(empty, P, "source_first", 0.1)


def test_expected_presence_mapping():
    assert expected_source_presence("source_first", 0.1) is True
    assert expected_source_presence("lossy", 0.6) is True
    assert expected_source_presence("lossy", 0.3) is False
    assert expected_source_presence("lossy_padded", 0.1) is False
    assert expected_source_presence("blank", 1.0) is False
    with pytest.raises(ValueError):
        expected_source_presence("sourcefirst", 0.1)
