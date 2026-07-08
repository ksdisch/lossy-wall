"""test_logic.py — the M4 logic family's re-typed problems and its judge-free text
readout, pinned by hand. No network, no model.

Two load-bearing things get guarded here, both under D6 (re-type verbatim) and the
project's judge-free-scoring rule:

  1. The re-typing of the author's PROBLEMS_LOGIC / FACTS_LOGIC / FOLLOWUPS_LOGIC — a
     wrong option, correct, or drift token would silently corrupt every logic cell built
     on that problem. `LOGIC_EXPECTED` hand-encodes each puzzle's answer space
     independently of problems.py, so a typo in the port fails against this table.
  2. The closed-option text scorer + the recov/inherit/novel/abst taxonomy. A token
     outside the problem's own option set must read as an ABSTENTION, never a phantom
     commit — the word-answer analogue of the arithmetic parser-bug guard in
     test_grader.py. reclaim == recov is what the D25 gap gate counts.
"""
from __future__ import annotations

from grader import (ABST, INHERIT, LOGIC_BUCKETS, NOVEL, RECOV, classify_logic,
                    parse_answer_word, score_text, took_logic)
from problems import CANONICAL_LOGIC, FOLLOWUPS_LOGIC

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
