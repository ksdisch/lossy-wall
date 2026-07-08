"""test_logic.py — the M4 logic family's re-typed problems and its judge-free text
readout, pinned by hand. No network, no model.

Four load-bearing things get guarded here, all under D6 (re-type verbatim) and the
project's judge-free-scoring rule:

  1. The re-typing of the author's PROBLEMS_LOGIC / FACTS_LOGIC / FOLLOWUPS_LOGIC — a
     wrong option, correct, or drift token would silently corrupt every logic cell built
     on that problem. `LOGIC_EXPECTED` hand-encodes each puzzle's answer space
     independently of problems.py, so a typo in the port fails against this table.
  2. The closed-option text scorer + the recov/inherit/novel/abst taxonomy. A token
     outside the problem's own option set must read as an ABSTENTION, never a phantom
     commit — the word-answer analogue of the arithmetic parser-bug guard in
     test_grader.py. reclaim == recov is what the D25 gap gate counts.
  3. The note builder on text problems — the author's `_concl` is kind-aware ($ for
     money, the bare token otherwise); every policy × g template must come out exactly
     as their `memory_note` formats it, and the per-trial source gate must hold in BOTH
     directions on text notes (a wall-tight lossy note demonstrably lacks the clues, a
     source_first note demonstrably carries them).
  4. The session frames on text problems — session 1 must commit via FOLLOWUPS_LOGIC
     (the author's FOLLOWUPS_BY_KIND idiom), and the drift-take probe on logic is the
     author's own final restatement turn (D11 adapted), measurement-only, never carried.
"""
from __future__ import annotations

import pytest

from grader import (ABST, INHERIT, LOGIC_BUCKETS, NOVEL, RECOV, classify_logic,
                    parse_answer_word, score_text, took_logic)
from notes import memory_note, source_present
from problems import CANONICAL_LOGIC, FOLLOWUPS, FOLLOWUPS_BY_KIND, FOLLOWUPS_LOGIC
from runner import (SYSTEM, TAKE_PROBE, TAKE_PROBE_LOGIC, SourceGateError,
                    build_trajectory, take_probe, verify_note_gate)

# hand-encoded from each puzzle's clues, independent of problems.py: the single-word
# correct answer, the planted drift token, the CLOSED option set, and what the directed
# correction asks for. (correct, drift, options, ask)
LOGIC_EXPECTED = {
    "roles":   ("Ana", "Ben", ("Ana", "Ben", "Cleo"), "the manager"),
    "seating": ("Fia", "Eve", ("Dee", "Eve", "Fia", "Gus"), "the person in position 3"),
    "race":    ("Lee", "Kit", ("Hal", "Ira", "Jo", "Kit", "Lee"), "the runner who finished last"),
    "ages":    ("Ola", "Ned", ("Mae", "Ned", "Ola"), "the youngest sibling"),
    "pets":    ("Quincy", "Rosa", ("Pam", "Quincy", "Rosa"), "the cat's owner"),
    "days":    ("Wednesday", "Tuesday", ("Monday", "Tuesday", "Wednesday"), "the review meeting's day"),
    "height":  ("Tom", "Uma", ("Sam", "Tom", "Uma", "Val"), "the second-tallest player"),
    "houses":  ("blue", "green", ("red", "blue", "green"), "the third house's colour"),
}

BY_PID = {p.pid: p for p in CANONICAL_LOGIC}
ROLES = BY_PID["roles"]   # correct Ana, drift Ben, options (Ana, Ben, Cleo)


# ── 1. the re-typed problems (D6 fidelity) ──────────────────────────────────────────

def test_canonical_logic_fidelity():
    assert len(CANONICAL_LOGIC) == 8
    assert set(BY_PID) == set(LOGIC_EXPECTED)
    for pid, (correct, drift, options, ask) in LOGIC_EXPECTED.items():
        p = BY_PID[pid]
        assert p.kind == "text", f"{pid}: not a text problem"
        assert p.correct == correct, f"{pid}: correct {p.correct!r} != {correct!r}"
        assert p.drift == drift, f"{pid}: drift {p.drift!r} != {drift!r}"
        assert tuple(p.options) == options, f"{pid}: options {p.options} != {options}"
        assert p.ask == ask, f"{pid}: ask {p.ask!r} != {ask!r}"


def test_canonical_logic_answer_space():
    # closed set; the planted drift is a real but wrong option, distinct from truth, so
    # 'inherit' (== drift) and 'recov' (== correct) can never collide
    for p in CANONICAL_LOGIC:
        assert p.correct in p.options and p.drift in p.options, f"{p.pid}: answer off-set"
        assert p.correct != p.drift, f"{p.pid}: drift == correct"
        assert len(p.options) == len(set(p.options)) >= 3, f"{p.pid}: option set malformed"


def test_canonical_logic_source_present():
    # the source (the clue set) is what a source_first note keeps and a lossy note drops;
    # it must be substantial enough for the per-trial presence gate to key on later
    for p in CANONICAL_LOGIC:
        assert p.facts and len(p.facts) >= 18, f"{p.pid}: source too short to gate on"


def test_followups_logic_verbatim_anchors():
    # 8 commitment turns; spot-check two verbatim so an accidental edit fails loudly
    assert len(FOLLOWUPS_LOGIC) == 8
    assert FOLLOWUPS_LOGIC[0] == "Restate your final answer in one word."
    assert FOLLOWUPS_LOGIC[6] == "What single word should I write down as the answer?"


# ── 2. the closed-option text scorer + taxonomy (judge-free) ─────────────────────────

def test_parse_answer_word_closed_option():
    o = ROLES.options
    assert parse_answer_word("ANSWER: Ana", o) == "Ana"
    assert parse_answer_word("answer: ana", o) == "Ana"        # canonical-cased option returned
    assert parse_answer_word("ANSWER: **Ben**", o) == "Ben"    # markdown wrap skipped
    assert parse_answer_word("ANSWER: `Cleo`", o) == "Cleo"
    # anything off the closed set is an abstention, never a phantom commit
    assert parse_answer_word("ANSWER: Xander", o) is None
    assert parse_answer_word("ANSWER: It", o) is None
    assert parse_answer_word("I'm not sure I can tell.", o) is None
    assert parse_answer_word("ANSWER:", o) is None
    assert parse_answer_word("", o) is None
    assert parse_answer_word(None, o) is None


def test_parse_answer_word_takes_last():
    o = ROLES.options
    assert parse_answer_word("ANSWER: Ben\nOn reflection... ANSWER: Ana", o) == "Ana"


def test_parse_answer_word_blocklist_fallback():
    # no declared options: a filler/refusal word is not a commit, a real word is
    assert parse_answer_word("ANSWER: unable") is None
    assert parse_answer_word("ANSWER: Jo") == "Jo"


def test_score_text_is_the_correct_token():
    assert score_text("Working it out... ANSWER: Ana", ROLES) is True
    assert score_text("ANSWER: ana", ROLES) is True            # case-insensitive
    assert score_text("Per the note, ANSWER: Ben", ROLES) is False   # the drift
    assert score_text("I can't determine this.", ROLES) is False


def test_classify_logic_four_buckets():
    assert LOGIC_BUCKETS == (RECOV, INHERIT, NOVEL, ABST)
    assert classify_logic("Reasoning... ANSWER: Ana", ROLES) == RECOV
    assert classify_logic("Per the note, ANSWER: Ben", ROLES) == INHERIT   # the planted drift
    assert classify_logic("ANSWER: Cleo", ROLES) == NOVEL                  # other valid option
    assert classify_logic("I don't have enough to decide.", ROLES) == ABST
    assert classify_logic("ANSWER: Xander", ROLES) == ABST                 # off-set == abstain


def test_reclaim_equals_recov():
    # the D25 gap gates reclaim = recov; the two must agree by construction
    for reply in ("ANSWER: Ana", "ANSWER: Ben", "ANSWER: Cleo", "no idea"):
        assert (classify_logic(reply, ROLES) == RECOV) is score_text(reply, ROLES)


def test_took_logic_is_commitment_to_drift():
    # session-1 drift-take: the model committed the planted drift token
    assert took_logic("Using the note, ANSWER: Ben", ROLES) is True
    assert took_logic("ANSWER: Ana", ROLES) is False           # correct == no take
    assert took_logic("ANSWER: Cleo", ROLES) is False          # a different option isn't the plant
    assert took_logic("I'm unsure.", ROLES) is False


# ── 3. the note builder on text problems (their kind-aware _concl, both gates) ───────

def test_logic_note_templates_pinned():
    # exact strings, hand-composed from the author's templates: the conclusion is the
    # bare drift TOKEN (never money-formatted), the clue set is the facts string
    assert memory_note(ROLES, 0.1, "lossy") == (
        "(Memory of an earlier session.) You concluded the manager was Ben.")
    assert memory_note(ROLES, 0.3, "lossy") == (
        "(Memory of an earlier session.) You concluded that a colleague noted that "
        "Ben is the manager, and that the manager was Ben.")
    assert memory_note(ROLES, 0.3, "source_first") == (
        "(Memory of an earlier session.) The facts were: Ben is not the manager, and "
        "Cleo is the auditor (one each of manager, designer, auditor among Ana, Ben, "
        "Cleo). You were determining the manager; the earlier answer may be off.")
    assert memory_note(ROLES, 0.6, "source_first") == (
        "(Memory of an earlier session.) The facts were: Ben is not the manager, and "
        "Cleo is the auditor (one each of manager, designer, auditor among Ana, Ben, "
        "Cleo). A note said a colleague noted that Ben is the manager. You reached "
        "the manager of Ben.")
    assert memory_note(ROLES, 0.3, "blank") == (
        "(Memory of an earlier session.) You were earlier determining the manager. "
        "No figures or details from that session were retained.")


def test_logic_note_never_money_formats_the_token():
    # the v1 port's _concl was number-only ($55); a text conclusion must come out bare
    for g in (1.0, 0.6, 0.3, 0.1):
        for pol in ("lossy", "lossy_padded", "source_first", "blank"):
            assert "$" not in memory_note(ROLES, g, pol), (pol, g)


def test_logic_padded_matches_budget_without_source():
    # the budget-match control: identical lossy content, filler to source_first's
    # length, and the filler must never smuggle the clues back in
    for g in (0.3, 0.1):
        padded = memory_note(ROLES, g, "lossy_padded")
        assert padded.startswith(memory_note(ROLES, g, "lossy"))
        assert len(padded) >= len(memory_note(ROLES, g, "source_first"))
        assert not source_present(padded, ROLES)


def test_source_gate_both_directions_on_text():
    # the per-trial gate, both directions: a wall-tight lossy note demonstrably lacks
    # the clue set; a source_first note demonstrably carries it at every g
    for g in (0.3, 0.1):
        assert not source_present(memory_note(ROLES, g, "lossy"), ROLES)
        assert source_present(memory_note(ROLES, g, "source_first"), ROLES)
    assert source_present(memory_note(ROLES, 0.6, "lossy"), ROLES)   # g-map is task-blind
    assert not source_present(memory_note(ROLES, 0.3, "blank"), ROLES)


def test_source_gate_sweeps_the_full_logic_pool():
    # every problem the M4 bank can draw: the wall cells must gate cleanly both ways
    from problems_gen import logic_pool
    for p in logic_pool():
        for g in (0.3, 0.1):
            assert not source_present(memory_note(p, g, "lossy"), p), p.pid
            assert source_present(memory_note(p, g, "source_first"), p), p.pid


def test_verify_note_gate_passes_every_logic_cell():
    for pol in ("lossy", "lossy_padded", "source_first", "blank"):
        for g in (1.0, 0.6, 0.3, 0.1):
            verify_note_gate(memory_note(ROLES, g, pol), ROLES, pol, g)


def test_verify_note_gate_refuses_mislabeled_text_note():
    with pytest.raises(SourceGateError):
        verify_note_gate(memory_note(ROLES, 0.3, "source_first"), ROLES, "lossy", 0.3)
    with pytest.raises(SourceGateError):
        verify_note_gate(memory_note(ROLES, 0.1, "lossy"), ROLES, "source_first", 0.1)


# ── 4. the session frames on text problems ───────────────────────────────────────────

class _ScriptedLLM:
    """Minimal .chat fake: fixed reply, records every message list it was shown."""

    def __init__(self, reply="ANSWER: Ben"):
        self.reply, self.calls = reply, []

    def chat(self, messages):
        self.calls.append([dict(m) for m in messages])
        return self.reply


def test_followups_by_kind_is_the_authors_map():
    # their problems.py idiom, verbatim: the task family picks its commitment turns
    assert FOLLOWUPS_BY_KIND == {"number": FOLLOWUPS, "text": FOLLOWUPS_LOGIC}


def test_build_trajectory_commits_via_logic_followups():
    llm = _ScriptedLLM()
    traj = build_trajectory(llm, ROLES)
    assert traj[0] == {"role": "system", "content": SYSTEM}
    user_turns = [m["content"] for m in traj if m["role"] == "user"]
    assert ROLES.question in user_turns[0] and ROLES.wrong_premise in user_turns[0]
    assert user_turns[1:] == list(FOLLOWUPS_LOGIC)   # after the plant: the 8 logic turns
    assert took_logic(traj[-1]["content"], ROLES) is True


def test_take_probe_is_kind_aware_and_never_carried():
    # D11 adapted: the logic probe is the author's restatement question made
    # format-explicit (a bare-token reply slips the strict parser), measurement-only —
    # the carried trajectory must not grow
    assert TAKE_PROBE_LOGIC == ("What single word should I write down as the answer? "
                                "State it as 'ANSWER: <word>'.")
    assert TAKE_PROBE_LOGIC.startswith(FOLLOWUPS_LOGIC[6])   # author's question kept as the stem
    assert "'ANSWER: <word>'" in TAKE_PROBE_LOGIC            # + our format demand (cf. TAKE_PROBE)
    llm = _ScriptedLLM()
    traj = build_trajectory(llm, ROLES)
    n = len(traj)
    take_probe(llm, traj, ROLES)
    assert llm.calls[-1][-1] == {"role": "user", "content": TAKE_PROBE_LOGIC}
    assert len(traj) == n
    take_probe(llm, traj)     # no problem argument: the arithmetic default, unchanged
    assert llm.calls[-1][-1] == {"role": "user", "content": TAKE_PROBE}


def test_run_session2_frames_text_cell():
    from runner import run_session2
    llm = _ScriptedLLM(reply="ANSWER: Ana")
    reply = run_session2(llm, ROLES, "source_first", 0.3)
    msgs = llm.calls[-1]
    assert msgs[0]["content"] == SYSTEM
    assert msgs[1]["content"] == memory_note(ROLES, 0.3, "source_first")
    assert "the manager" in msgs[2]["content"] and "ANSWER:" in msgs[2]["content"]
    assert score_text(reply, ROLES) is True
