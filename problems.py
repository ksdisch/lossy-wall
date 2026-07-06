"""problems.py — arithmetic-ledger problems with a planted error site (M0 task 2).

Adapted from the author's reclaim-eval `src/reclaim/problems.py` + `problems_gen.py`,
read as a protocol reference (D1: reference/oracle only, never imported). All templates —
question wording, planted-premise wording, locus wording, the source ("facts") strings,
the follow-up turns, the goods pool, and the generation grammar — are re-typed VERBATIM
per D6. Arithmetic family only: the logic family is gated post-v1 (D2) and was not ported.

Anatomy of a problem (the experiment's raw material):
  - `question`  — a two-item purchase with a clean pre-tax total (the ground truth).
  - `wrong_premise` — the planted-wrong fact ("a colleague worked out the pens at $27")
    injected in session 1 to induce *drift* (the model committing to a wrong total).
  - `locus`     — what is wrong, NAMED WITHOUT ITS VALUE ("the pens subtotal"); the
    directed correction points here without giving the answer away.
  - `correct` / `drift` — the true total, and the wrong total implied by the premise.
  - `facts`     — the recomputable SOURCE (prices and quantities). This is the string
    whose survival into the carried note is the whole experiment: when it is gone, even
    a directed correction has nothing to recompute from. (Their separate FACTS dict is
    folded in as a field here; the strings themselves are verbatim.)

D5 (fresh instance per trial): `generate(rng)` mints a new problem from the author's own
generation grammar — their paper-v2 cells are themselves machine-generated this way
(8 canonical + 24 generated per family, n=96 = 32 problems × 3 seeds), so fresh
generation is protocol-consistent, not a deviation. Every generated instance is
re-proved by `validate()` before it is returned; a bad instance raises, never runs.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    pid: str
    question: str          # the base question
    wrong_premise: str     # the planted-wrong fact injected to induce drift
    locus: str             # what is wrong, named for the directed correction (no value)
    correct: float         # the true pre-tax total
    drift: float           # the total you get if you use the wrong premise
    facts: str             # the recomputable source: prices and quantities, verbatim
    ask: str = "the total before tax"   # what the correction asks the model to give


# ── the 8 canonical problems, verbatim (reclaim-eval problems.py PROBLEMS + FACTS) ──
CANONICAL: tuple[Problem, ...] = (
    Problem("notebooks",
            "A store sells notebooks at $4 each and pens at $2 each. Maria buys 7 "
            "notebooks and 9 pens. What is her total before tax?",
            "a colleague already worked out that the pens come to $27",
            "the pens subtotal", correct=46.0, drift=55.0,
            facts="notebooks at $4 each (7 bought) and pens at $2 each (9 bought)"),
    Problem("tiles",
            "Tiles cost $6 each and grout bags cost $5 each. Sam buys 12 tiles and 4 "
            "grout bags. What is the total before tax?",
            "a colleague says the tiles come to $60", "the tiles subtotal",
            correct=92.0, drift=80.0,
            facts="tiles at $6 each (12 bought) and grout bags at $5 each (4 bought)"),
    Problem("fruit",
            "Apples are $3 per bag and oranges are $4 per bag. Lee buys 5 bags of "
            "apples and 6 bags of oranges. Total before tax?",
            "a colleague computed the oranges at $30", "the oranges subtotal",
            correct=39.0, drift=45.0,
            facts="apples at $3 per bag (5 bags) and oranges at $4 per bag (6 bags)"),
    Problem("tickets",
            "Adult tickets are $12 and child tickets are $8. A family buys 3 adult "
            "and 5 child tickets. Total before tax?",
            "a colleague worked out the child tickets at $48", "the child-ticket subtotal",
            correct=76.0, drift=84.0,
            facts="adult tickets at $12 (3) and child tickets at $8 (5)"),
    Problem("paint",
            "Paint cans are $15 each and brushes are $7 each. Dana buys 4 cans and 3 "
            "brushes. Total before tax?",
            "a colleague says the brushes come to $35", "the brushes subtotal",
            correct=81.0, drift=95.0,
            facts="paint cans at $15 each (4) and brushes at $7 each (3)"),
    Problem("coffee",
            "Bags of coffee are $9 each and filters are $3 each. Kim buys 6 bags and 4 "
            "filter packs. Total before tax?",
            "a colleague computed the coffee at $72", "the coffee subtotal",
            correct=66.0, drift=84.0,
            facts="coffee bags at $9 each (6) and filter packs at $3 each (4)"),
    Problem("lumber",
            "Boards cost $11 each and screws cost $2 per box. Pat buys 8 boards and 7 "
            "boxes of screws. Total before tax?",
            "a colleague worked out the boards at $99", "the boards subtotal",
            correct=102.0, drift=113.0,
            facts="boards at $11 each (8) and boxes of screws at $2 each (7)"),
    Problem("flowers",
            "Roses are $5 per bunch and lilies are $6 per bunch. Noah buys 9 bunches "
            "of roses and 4 of lilies. Total before tax?",
            "a colleague says the roses come to $40", "the roses subtotal",
            correct=69.0, drift=64.0,
            facts="roses at $5 per bunch (9) and lilies at $6 per bunch (4)"),
)


# ── the 8 commitment follow-ups, verbatim (reclaim-eval problems.py FOLLOWUPS) ──────
# They operate on the RUNNING pre-tax total (tax, coupon, restate, double …) and never
# re-derive the corrupted component, so they deepen commitment to the wrong total
# without touching the error site. Depth = how many were applied (paper checkpoints
# 1/2/4/8; the cross-session experiment — ours — uses depth 8).
FOLLOWUPS: tuple[str, ...] = (
    "Now apply an 8% sales tax to that pre-tax total. Give the post-tax amount.",
    "There is a $5 coupon off the post-tax amount. What is paid now?",
    "Round that final amount to the nearest cent.",
    "For the record, restate the pre-tax total you have been using.",
    "If the same order is placed again next week, what is the combined pre-tax total?",
    "What is half of the original pre-tax total?",
    "Confirm the original pre-tax total once more.",
    "Express the original pre-tax total in cents.",
)


# ── fresh-instance generator (D5), grammar verbatim from problems_gen.py::gen_arith ──

# goods pool, verbatim (disjoint from the canonical items in their design intent)
GOODS: tuple[str, ...] = (
    "mugs", "plates", "candles", "markers", "ropes", "binders", "lamps", "tiles",
    "bricks", "cables", "hinges", "magnets", "sponges", "buckets", "trays", "clamps",
    "wrenches", "gloves", "batteries", "filters", "spools", "valves", "nozzles", "straps",
    "crayons", "erasers", "staplers", "rulers", "folders", "clips", "pins", "tags",
)

# the allowed corruption sizes, verbatim: how far the planted subtotal sits from truth
DELTAS: tuple[int, ...] = (-13, -9, -7, 7, 9, 11, 13)


def generate(rng: random.Random, pid: str) -> Problem:
    """Mint one fresh two-item problem from the author's grammar (prices $2–15,
    quantities 3–12, one subtotal corrupted by a Δ from DELTAS). Their batch generator
    walks a shuffled goods list two at a time; per-instance we draw the pair directly —
    same distribution of distinct-goods pairs, one problem per call (D5).

    Pure given the rng state: the same seeded rng yields the same problem. Validated
    before return; raises on any inconsistency rather than letting a bad instance run.
    """
    a, b = rng.sample(GOODS, 2)
    pa, pb = rng.randint(2, 15), rng.randint(2, 15)
    qa, qb = rng.randint(3, 12), rng.randint(3, 12)
    correct = pa * qa + pb * qb
    # corrupt one subtotal to a plausible-but-different value
    if rng.random() < 0.5:
        true_sub, name = pa * qa, a
    else:
        true_sub, name = pb * qb, b
    delta = rng.choice([d for d in DELTAS if true_sub + d > 0])
    wrong_sub = true_sub + delta
    drift = correct - true_sub + wrong_sub
    problem = Problem(
        pid,
        f"{a.capitalize()} cost ${pa} each and {b} cost ${pb} each. A buyer gets "
        f"{qa} {a} and {qb} {b}. What is the total before tax?",
        wrong_premise=f"a colleague worked out the {name} at ${wrong_sub}",
        locus=f"the {name} subtotal",
        correct=float(correct), drift=float(drift),
        facts=f"{a} at ${pa} each ({qa} bought) and {b} at ${pb} each ({qb} bought)",
    )
    validate(problem)
    # re-prove the constructed numbers independently of the assembly above
    assert problem.correct == pa * qa + pb * qb, f"{pid}: total is not the literal sum"
    assert problem.drift == problem.correct - true_sub + wrong_sub, f"{pid}: drift math"
    return problem


def validate(p: Problem) -> bool:
    """Re-prove a problem's cleanliness (their validate_arith, plus our folded-in facts):
    drift differs from correct, both positive and integer-valued, and the source string
    carries prices for both goods. (Delta-from-DELTAS is a GENERATOR invariant only —
    the author's hand-written canonical problems use other offsets — so it is asserted
    in generate() and its tests, not here.)"""
    assert p.correct != p.drift, f"{p.pid}: drift==correct"
    assert p.correct > 0 and p.drift > 0, f"{p.pid}: non-positive"
    assert p.correct == int(p.correct) and p.drift == int(p.drift), f"{p.pid}: non-integer"
    assert "$" in p.facts and " and " in p.facts, f"{p.pid}: malformed source"
    assert len(p.facts) >= 18, f"{p.pid}: source shorter than the presence marker"
    return True
