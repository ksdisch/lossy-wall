"""problems.py — arithmetic-ledger problems with a planted error site (M0 task 2).

Adapted from the author's reclaim-eval `src/reclaim/problems.py` + `problems_gen.py`,
read as a protocol reference (D1: reference/oracle only, never imported). All templates —
question wording, planted-premise wording, locus wording, the source ("facts") strings,
the follow-up turns, the goods pool, and the generation grammar — are re-typed VERBATIM
per D6. Both families are re-typed here: the arithmetic ledgers (v1) and — since M4
opened 2026-07-08 — the logic puzzles (CANONICAL_LOGIC / FOLLOWUPS_LOGIC).

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
    correct: float | str   # arithmetic: the true pre-tax total; logic: the correct word
    drift: float | str     # the value/token you get if you use the wrong premise
    facts: str             # the recomputable source: prices/quantities, or the clue set
    ask: str = "the total before tax"   # what the correction asks the model to give
    kind: str = "number"   # "number" (numeric tolerance) or "text" (closed-option word match)
    options: tuple = ()    # text tasks: the CLOSED set of valid answer tokens (this
                           # problem's own entities), validated against, not guessed at


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


# ── the logic family: constraint-deduction puzzles (M4; gated post-v1, opened 2026-07-08).
#    Re-typed VERBATIM from reclaim-eval problems.py PROBLEMS_LOGIC + FACTS_LOGIC (D6). Same
#    shape as the arithmetic family — a planted-wrong clue drifts a single-token answer that a
#    clean SOURCE of clues fully determines — but the recomputation is LOGICAL, not numeric
#    (their docstring: "the harder case for source_first: the source is a set of relations, not
#    a formula"). Each answer is one word from a CLOSED option set, so scoring stays judge-free.
#    FACTS_LOGIC (the recomputable clue set) is folded into each Problem's `facts`, as with the
#    arithmetic family. ────────────────────────────────────────────────────────────────────────
CANONICAL_LOGIC: tuple[Problem, ...] = (
    Problem("roles",
            "Three coworkers, Ana, Ben, and Cleo, each hold exactly one role: manager, "
            "designer, or auditor. Ben is not the manager. Cleo is the auditor. Who is "
            "the manager?",
            "a colleague noted that Ben is the manager", "Ben's role",
            correct="Ana", drift="Ben",
            facts="Ben is not the manager, and Cleo is the auditor (one each of manager, "
                  "designer, auditor among Ana, Ben, Cleo)",
            ask="the manager", kind="text", options=("Ana", "Ben", "Cleo")),
    Problem("seating",
            "Four friends sit in a row in positions 1 to 4, left to right: Dee, Eve, "
            "Fia, Gus. Dee is at position 1. Eve is immediately to the right of Dee. Gus "
            "is at position 4. Who is at position 3?",
            "a colleague says Eve is at position 3", "Eve's position",
            correct="Fia", drift="Eve",
            facts="Dee is at position 1, Eve is immediately right of Dee, and Gus is at "
                  "position 4 (positions 1 to 4 for Dee, Eve, Fia, Gus)",
            ask="the person in position 3", kind="text",
            options=("Dee", "Eve", "Fia", "Gus")),
    Problem("race",
            "Five runners finished a race: Hal, Ira, Jo, Kit, and Lee. Hal finished "
            "ahead of Ira. Ira finished ahead of Jo. Jo finished ahead of Kit. Kit "
            "finished ahead of Lee. Who finished last?",
            "a colleague says Kit finished behind Lee", "the Kit and Lee ordering",
            correct="Lee", drift="Kit",
            facts="Hal ahead of Ira, Ira ahead of Jo, Jo ahead of Kit, and Kit ahead of Lee",
            ask="the runner who finished last", kind="text",
            options=("Hal", "Ira", "Jo", "Kit", "Lee")),
    Problem("ages",
            "Three siblings are Mae, Ned, and Ola. Mae is older than Ned. Ola is younger "
            "than Ned. Who is the youngest?",
            "a colleague says Ned is younger than Ola", "the Ned and Ola age order",
            correct="Ola", drift="Ned",
            facts="Mae is older than Ned, and Ola is younger than Ned",
            ask="the youngest sibling", kind="text", options=("Mae", "Ned", "Ola")),
    Problem("pets",
            "Pam, Quincy, and Rosa each own exactly one pet: a cat, a dog, or a fish. "
            "Pam owns the dog. Quincy does not own the fish. Who owns the cat?",
            "a colleague says Quincy owns the fish", "Quincy's pet",
            correct="Quincy", drift="Rosa",
            facts="Pam owns the dog, and Quincy does not own the fish (cat, dog, fish, one "
                  "each among Pam, Quincy, Rosa)",
            ask="the cat's owner", kind="text", options=("Pam", "Quincy", "Rosa")),
    Problem("days",
            "Three meetings are each on a different day, Monday, Tuesday, or Wednesday: "
            "the budget meeting, the design meeting, and the review meeting. The budget "
            "meeting is on Monday. The design meeting is not on Wednesday. Which day is "
            "the review meeting?",
            "a colleague says the design meeting is on Wednesday", "the design meeting's day",
            correct="Wednesday", drift="Tuesday",
            facts="the budget meeting is on Monday, and the design meeting is not on "
                  "Wednesday (budget, design, review on Monday, Tuesday, Wednesday)",
            ask="the review meeting's day", kind="text",
            options=("Monday", "Tuesday", "Wednesday")),
    Problem("height",
            "Four players are ranked by height: Sam, Tom, Uma, and Val. Sam is taller "
            "than Tom. Tom is taller than Uma. Uma is taller than Val. Who is the second "
            "tallest?",
            "a colleague says Uma is taller than Tom", "the Tom and Uma height order",
            correct="Tom", drift="Uma",
            facts="Sam taller than Tom, Tom taller than Uma, and Uma taller than Val",
            ask="the second-tallest player", kind="text",
            options=("Sam", "Tom", "Uma", "Val")),
    Problem("houses",
            "Three houses in a row are painted red, blue, and green, one colour each. "
            "The first house is red. The blue house is not the middle one. What colour "
            "is the third house?",
            "a colleague says the blue house is the middle one", "the blue house's position",
            correct="blue", drift="green",
            facts="the first house is red, and the blue house is not the middle one (red, "
                  "blue, green, one each)",
            ask="the third house's colour", kind="text", options=("red", "blue", "green")),
)


# ── the 8 logic commitment follow-ups, verbatim (reclaim-eval problems.py FOLLOWUPS_LOGIC) ──
# They re-affirm the stated answer WITHOUT re-solving, so they deepen commitment to the
# committed (possibly drifted) token without re-deriving it from the clues. Depth 8, as arith.
FOLLOWUPS_LOGIC: tuple[str, ...] = (
    "Restate your final answer in one word.",
    "How confident are you in that answer? One short sentence.",
    "If someone asked you in passing, what would you say the answer is?",
    "For the record, repeat the answer you settled on.",
    "Summarise your conclusion in a short sentence.",
    "Confirm that answer once more.",
    "What single word should I write down as the answer?",
    "State the answer again, just to be sure.",
)
