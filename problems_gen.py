"""problems_gen.py — the M4 logic-family generators: 8 canonical → 32 problems.

Re-typed VERBATIM from the author's reclaim-eval `src/reclaim/problems_gen.py` (D6;
read as protocol reference per D1, never imported): the NAMES pool, the ITEMSETS pool,
both brute-force solvers, both generation grammars, and both validators. Their
problems.py expands each family at load — `gen_logic(12, seed=2)` +
`gen_assign(12, seed=3)`, validated, appended after the 8 canonical — which is exactly
what `logic_pool()` assembles here; the seeds are the author's own, so the same 24
generated puzzles come out (every rng call is kept in their exact order — reordering
one draw would silently mint a different problem set from the same seed).

Every generated puzzle is correct BY CONSTRUCTION and then re-proved: the clue chain is
brute-force-solved to a unique answer, the planted wrong clue is brute-force-solved to a
unique DIFFERENT answer, and instances failing either check are discarded (rejection
sampling), never patched. `validate_logic` / `validate_assign` re-prove each kept puzzle
from its OWN facts string, independent of generation — a bad instance raises, never runs.

Adaptations from their file, both documented in problems.py's port too:
  - their separate FACTS dict is folded into each Problem's `facts` field, so the
    validators here take just the problem list and read `p.facts`;
  - their `gen_arith` is not ported — v1's per-instance `problems.generate()` (D5)
    already carries the arithmetic grammar; this module is the logic expansion only.
"""
from __future__ import annotations

import random
import re
from itertools import permutations

from problems import CANONICAL_LOGIC, Problem

# the name pool, verbatim
NAMES = ["Ana", "Ben", "Cleo", "Dee", "Eve", "Fia", "Gus", "Hal", "Ira", "Jo", "Kit",
         "Lee", "Mae", "Ned", "Ola", "Pam", "Quinn", "Rosa", "Sam", "Tom", "Uma", "Val"]

# the assignment item pools, verbatim
ITEMSETS = [("manager", "designer", "auditor"), ("cat", "dog", "fish"),
            ("red", "blue", "green"), ("gold", "silver", "bronze"),
            ("tea", "coffee", "juice"), ("rose", "tulip", "daisy")]


# ── logic family: total-order (race) puzzles, brute-force verified ─────────────────
def _order_answer(names, ahead, query):
    """Unique answer to `query` over all orders satisfying `ahead` (X before Y), else None."""
    sols = set()
    for perm in permutations(names):
        idx = {n: i for i, n in enumerate(perm)}
        if all(idx[x] < idx[y] for x, y in ahead):
            sols.add(perm[-1] if query == "last" else perm[1])
    return next(iter(sols)) if len(sols) == 1 else None


def gen_logic(n: int, seed: int = 2) -> tuple[Problem, ...]:
    """n ordering puzzles: a clue chain fixes a unique answer; one reversed clue (the
    planted drift) yields a unique DIFFERENT answer. Both are verified by brute force
    before keeping."""
    rng = random.Random(seed)
    out, kept, tries = [], 0, 0
    while kept < n and tries < n * 80:
        tries += 1
        k = rng.choice([4, 5])
        order = rng.sample(NAMES, k)                         # true finish order, index 0 = first
        ahead = [(order[j], order[j + 1]) for j in range(k - 1)]   # full chain -> unique order
        query = rng.choice(["last", "second"])
        correct = _order_answer(order, ahead, query)
        if correct is None:
            continue
        j = rng.randrange(k - 1)                              # reverse one consecutive clue
        a, b = order[j], order[j + 1]
        corrupt = [p for p in ahead if p != (a, b)] + [(b, a)]
        drift = _order_answer(order, corrupt, query)
        if drift is None or drift == correct:
            continue
        listed = rng.sample(order, k)                        # list names NOT in finish order
        clue_txt = ". ".join(f"{x} finished ahead of {y}" for x, y in ahead)
        ask = "the runner who finished last" if query == "last" else "the runner who finished second"
        out.append(Problem(
            f"gen_l{kept}",
            f"{k} runners finished a race: {', '.join(listed)}. {clue_txt}. "
            f"Who finished {'last' if query == 'last' else 'second'}?",
            wrong_premise=f"a colleague says {b} finished ahead of {a}",
            locus=f"the {a}-versus-{b} finish order",
            correct=correct, drift=drift,
            facts=", ".join(f"{x} ahead of {y}" for x, y in ahead),
            ask=ask, kind="text", options=tuple(order)))
        kept += 1
    if kept < n:
        raise RuntimeError(f"only generated {kept}/{n} logic problems")
    return tuple(out)


def validate_logic(problems) -> bool:
    """Re-prove each puzzle from its OWN clue source (facts), independent of generation."""
    for p in problems:
        # rebuild the ahead-pairs from the source string and re-solve
        pairs = [tuple(s.strip().split(" ahead of ")) for s in p.facts.split(",")]
        query = "last" if "last" in p.ask else "second"
        names = sorted({n for pr in pairs for n in pr})
        ans = _order_answer(names, pairs, query)
        assert ans == p.correct, f"{p.pid}: source solves to {ans}, not {p.correct}"
        assert p.drift != p.correct, f"{p.pid}: drift==correct"
        assert isinstance(p.correct, str) and isinstance(p.drift, str), f"{p.pid}: non-token answer"
    return True


# ── logic family, part 2: assignment puzzles (who has item X), brute-force verified ──
def _assign_answer(people, items, pos, neg, query_item):
    """Unique person holding query_item over all bijections people->items satisfying clues, else None."""
    sols = set()
    for perm in permutations(items):
        a = dict(zip(people, perm))
        if all(a[p] == it for p, it in pos) and all(a[p] != it for p, it in neg):
            who = [p for p in people if a[p] == query_item]
            if len(who) == 1:
                sols.add(who[0])
    return next(iter(sols)) if len(sols) == 1 else None


def gen_assign(n: int, seed: int = 3) -> tuple[Problem, ...]:
    """n assignment puzzles: a clue set fixes a unique 'who has item X'; one flipped clue
    (the drift) yields a unique DIFFERENT person. Both verified by brute force before
    keeping."""
    rng = random.Random(seed)
    out, kept, tries = [], 0, 0
    while kept < n and tries < n * 120:
        tries += 1
        k = 3
        people = rng.sample(NAMES, k)
        items = list(rng.choice(ITEMSETS))
        true = dict(zip(people, rng.sample(items, k)))         # true bijection
        # one positive (a person's true item) + one negative (a person is-not a wrong item)
        pp = rng.choice(people)
        npers = rng.choice([p for p in people if p != pp])
        nitem = rng.choice([it for it in items if it != true[npers]])
        pos, neg = [(pp, true[pp])], [(npers, nitem)]
        query_item = rng.choice([it for it in items if it != true[pp]])  # ask about an unstated item
        correct = _assign_answer(people, items, pos, neg, query_item)
        if correct is None:
            continue
        # plant drift: flip the negative into a (false) positive -> different unique holder, if any
        cpos, cneg = pos + [(npers, nitem)], []
        drift = _assign_answer(people, items, cpos, cneg, query_item)
        if drift is None or drift == correct:
            continue
        clue_txt = (f"{pp} has the {true[pp]}. {npers} does not have the {nitem}")
        out.append(Problem(
            f"gen_s{kept}",
            f"{', '.join(people)} each have exactly one of: {', '.join(items)}. {clue_txt}. "
            f"Who has the {query_item}?",
            wrong_premise=f"a colleague says {npers} has the {nitem}",
            locus=f"what {npers} has",
            correct=correct, drift=drift,
            facts=(f"{pp} has {true[pp]}; {npers} not {nitem}; "
                   f"domain {'/'.join(items)} among {'/'.join(people)}"),
            ask=f"the person with the {query_item}", kind="text",
            options=tuple(people)))
        kept += 1
    if kept < n:
        raise RuntimeError(f"only generated {kept}/{n} assignment problems")
    return tuple(out)


def validate_assign(problems) -> bool:
    """Re-prove each assignment puzzle from its own clue source, independent of generation."""
    for p in problems:
        src = p.facts
        pos = re.findall(r"(\w+) has (\w+);", src)
        neg = re.findall(r"(\w+) not (\w+);", src)
        dom = re.search(r"domain ([\w/]+) among ([\w/]+)", src)
        items, people = dom.group(1).split("/"), dom.group(2).split("/")
        qi = p.ask.split("with the ")[1]
        assert _assign_answer(people, items, pos, neg, qi) == p.correct, f"{p.pid}: source mismatch"
        assert p.drift != p.correct, f"{p.pid}: drift==correct"
    return True


def logic_pool() -> tuple[Problem, ...]:
    """The M4 logic problem pool exactly as the author's problems.py assembles it:
    the 8 canonical puzzles + 12 generated ordering + 12 generated assignment = 32,
    the generated sets validated before use (their seeds, their order)."""
    gl = gen_logic(12, seed=2)
    validate_logic(gl)
    gs = gen_assign(12, seed=3)
    validate_assign(gs)
    return CANONICAL_LOGIC + gl + gs
