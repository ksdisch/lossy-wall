"""test_problems.py — the canonical problems re-proved by hand, and the generator's
invariants. No network, no model.

The canonical checks guard the RE-TYPING itself (D6 says templates come over verbatim —
a typo in a price or a planted value would silently corrupt every cell built on that
problem). Each problem's components were hand-encoded here from the question text, and
correct/drift are re-derived: correct = a·qa + b·qb, drift = correct − true_sub + planted.
"""
from __future__ import annotations

import random

from problems import CANONICAL, DELTAS, FOLLOWUPS, GOODS, generate, validate

# (price_a, qty_a, price_b, qty_b, planted_wrong_subtotal, corrupted_item_index)
# hand-read from each canonical question + premise; the corrupted item is 0=first, 1=second
COMPONENTS = {
    "notebooks": (4, 7, 2, 9, 27, 1),    # pens 18 -> planted 27
    "tiles":     (6, 12, 5, 4, 60, 0),   # tiles 72 -> planted 60
    "fruit":     (3, 5, 4, 6, 30, 1),    # oranges 24 -> planted 30
    "tickets":   (12, 3, 8, 5, 48, 1),   # child 40 -> planted 48
    "paint":     (15, 4, 7, 3, 35, 1),   # brushes 21 -> planted 35
    "coffee":    (9, 6, 3, 4, 72, 0),    # coffee 54 -> planted 72
    "lumber":    (11, 8, 2, 7, 99, 0),   # boards 88 -> planted 99
    "flowers":   (5, 9, 6, 4, 40, 0),    # roses 45 -> planted 40
}


def test_canonical_totals_reprove():
    assert len(CANONICAL) == 8
    for p in CANONICAL:
        pa, qa, pb, qb, planted, which = COMPONENTS[p.pid]
        subs = (pa * qa, pb * qb)
        correct = sum(subs)
        drift = correct - subs[which] + planted
        assert p.correct == correct, f"{p.pid}: correct is {p.correct}, re-derived {correct}"
        assert p.drift == drift, f"{p.pid}: drift is {p.drift}, re-derived {drift}"


def test_canonical_shape():
    pids = [p.pid for p in CANONICAL]
    assert len(set(pids)) == 8
    for p in CANONICAL:
        validate(p)
        # the planted value appears in the premise; the locus never carries a value
        planted = COMPONENTS[p.pid][4]
        assert f"${planted}" in p.wrong_premise
        assert "$" not in p.locus
        assert p.ask == "the total before tax"


def test_followups_verbatim_anchors():
    # 8 turns; spot-check two verbatim so accidental edits fail loudly
    assert len(FOLLOWUPS) == 8
    assert FOLLOWUPS[0] == ("Now apply an 8% sales tax to that pre-tax total. Give the "
                            "post-tax amount.")
    assert FOLLOWUPS[6] == "Confirm the original pre-tax total once more."


def test_generator_invariants():
    rng = random.Random(42)
    seen_questions = set()
    for i in range(200):
        p = generate(rng, pid=f"gen-{i}")
        validate(p)  # generate() already validates; re-proving here is the test's job
        assert p.pid == f"gen-{i}"
        # the corruption is one of the allowed deltas, applied to exactly one subtotal
        assert abs(int(p.drift - p.correct)) in {abs(d) for d in DELTAS}
        # both goods named in the source string and the question
        named = [g for g in GOODS if f" {g} " in f" {p.facts} "]
        assert len(named) >= 2, f"{p.pid}: source names {named}"
        # premise carries a $ value; locus names the component without a value
        assert "$" in p.wrong_premise and "$" not in p.locus
        seen_questions.add(p.question)
    # fresh instances: numbers/goods vary (D5's whole point). 200 draws from this
    # grammar collide rarely; near-total uniqueness is the independence we need.
    assert len(seen_questions) > 190


def test_generator_deterministic_given_seed():
    a = generate(random.Random(7), pid="x")
    b = generate(random.Random(7), pid="x")
    assert a == b  # pure given the rng state: reproducible runs from a recorded seed
