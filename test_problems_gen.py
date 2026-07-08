"""test_problems_gen.py — the M4 logic generators (the 8→32 expansion), pinned by hand.
No network, no model.

The author expands each family from 8 canonical to 32 problems so a reclaim cell can
reach n=96 without hand-arithmetic risk (their problems.py: gen_logic(12, seed=2) +
gen_assign(12, seed=3), validated at load). We re-type the two logic generators per D6
and re-prove the SAME guarantees here, three layers deep:

  1. Determinism — the author's seeds are part of the protocol: the same seed must mint
     the same problems every run, or the M4 bank's problem schedule silently shifts.
  2. Independent re-solve — this file carries its OWN brute-force solvers and re-derives
     every generated puzzle's correct answer from the problem's facts string, and its
     drift token from the planted wrong premise. The generator's solver never grades
     itself (the M0 lesson: scoring corruption lives where a component checks its own
     work).
  3. The validators — validate_logic / validate_assign must pass the generated sets and
     must RAISE on a tampered problem (a wrong answer token can never slip into a run).
"""
from __future__ import annotations

import re
from dataclasses import replace
from itertools import permutations

import pytest

from problems import CANONICAL_LOGIC
from problems_gen import (gen_assign, gen_logic, logic_pool, validate_assign,
                          validate_logic)


# ── independent solvers (this file's own, never the generator's) ─────────────────────

def solve_order(pairs, query, names):
    """Unique answer over all orders satisfying every (x ahead of y) pair, else None."""
    sols = set()
    for perm in permutations(names):
        idx = {n: i for i, n in enumerate(perm)}
        if all(idx[x] < idx[y] for x, y in pairs):
            sols.add(perm[-1] if query == "last" else perm[1])
    return next(iter(sols)) if len(sols) == 1 else None


def solve_assign(people, items, pos, neg, query_item):
    """Unique person holding query_item over all bijections satisfying the clues."""
    sols = set()
    for perm in permutations(items):
        a = dict(zip(people, perm))
        if all(a[p] == it for p, it in pos) and all(a[p] != it for p, it in neg):
            who = [p for p in people if a[p] == query_item]
            if len(who) == 1:
                sols.add(who[0])
    return next(iter(sols)) if len(sols) == 1 else None


def order_pairs(p):
    """The clue pairs as the facts string carries them: 'X ahead of Y, …'."""
    return [tuple(s.strip().split(" ahead of ")) for s in p.facts.split(",")]


LOGIC = gen_logic(12, seed=2)
ASSIGN = gen_assign(12, seed=3)


# ── 1. determinism: the seed IS the schedule ─────────────────────────────────────────

def test_generators_are_deterministic():
    assert gen_logic(12, seed=2) == LOGIC
    assert gen_assign(12, seed=3) == ASSIGN


def test_seed_changes_problems():
    # a different seed must not silently reproduce the same set
    assert gen_logic(12, seed=99) != LOGIC


# ── 2. shape: counts, pids, closed answer sets ───────────────────────────────────────

def test_gen_logic_shape():
    assert len(LOGIC) == 12
    assert [p.pid for p in LOGIC] == [f"gen_l{i}" for i in range(12)]
    for p in LOGIC:
        assert p.kind == "text", f"{p.pid}: not a text problem"
        assert len(p.options) in (4, 5), f"{p.pid}: k off the author's 4/5 grammar"
        assert p.correct in p.options and p.drift in p.options, f"{p.pid}: answer off-set"
        assert p.correct != p.drift, f"{p.pid}: drift == correct"
        assert len(p.facts) >= 18, f"{p.pid}: source too short to gate on"
        assert p.ask in ("the runner who finished last", "the runner who finished second")


def test_gen_assign_shape():
    assert len(ASSIGN) == 12
    assert [p.pid for p in ASSIGN] == [f"gen_s{i}" for i in range(12)]
    for p in ASSIGN:
        assert p.kind == "text", f"{p.pid}: not a text problem"
        assert len(p.options) == 3, f"{p.pid}: assignment puzzles are 3-person"
        assert p.correct in p.options and p.drift in p.options, f"{p.pid}: answer off-set"
        assert p.correct != p.drift, f"{p.pid}: drift == correct"
        assert len(p.facts) >= 18, f"{p.pid}: source too short to gate on"
        assert p.ask.startswith("the person with the ")


# ── 3. independent re-solve: facts → correct, wrong premise → drift ──────────────────

def test_gen_logic_facts_solve_to_correct():
    # the facts string alone (what a source_first note carries) must fully determine
    # the correct answer — that is the whole source_first mechanism on logic
    for p in LOGIC:
        pairs = order_pairs(p)
        query = "last" if "last" in p.ask else "second"
        names = sorted({n for pr in pairs for n in pr})
        assert solve_order(pairs, query, names) == p.correct, f"{p.pid}: source mismatch"


def test_gen_logic_planted_premise_solves_to_drift():
    # reversing exactly the planted clue must land on the drift token — otherwise the
    # plant would not be a coherent wrong world and 'inherit' would be unreadable
    for p in LOGIC:
        m = re.fullmatch(r"a colleague says (\w+) finished ahead of (\w+)", p.wrong_premise)
        assert m, f"{p.pid}: premise off the author's template"
        b, a = m.groups()
        pairs = order_pairs(p)
        assert (a, b) in pairs, f"{p.pid}: premise does not reverse a real clue"
        corrupt = [pr for pr in pairs if pr != (a, b)] + [(b, a)]
        query = "last" if "last" in p.ask else "second"
        names = sorted({n for pr in pairs for n in pr})
        assert solve_order(corrupt, query, names) == p.drift, f"{p.pid}: drift mismatch"


def test_gen_assign_facts_solve_to_correct():
    for p in ASSIGN:
        pos = re.findall(r"(\w+) has (\w+);", p.facts)
        neg = re.findall(r"(\w+) not (\w+);", p.facts)
        dom = re.search(r"domain ([\w/]+) among ([\w/]+)", p.facts)
        items, people = dom.group(1).split("/"), dom.group(2).split("/")
        qi = p.ask.split("with the ")[1]
        assert solve_assign(people, items, pos, neg, qi) == p.correct, \
            f"{p.pid}: source mismatch"


def test_gen_assign_planted_premise_solves_to_drift():
    # the plant turns the negative clue into a (false) positive; under that corrupted
    # clue set the unique holder must be the drift token
    for p in ASSIGN:
        m = re.fullmatch(r"a colleague says (\w+) has the (\w+)", p.wrong_premise)
        assert m, f"{p.pid}: premise off the author's template"
        npers, nitem = m.groups()
        pos = re.findall(r"(\w+) has (\w+);", p.facts)
        neg = re.findall(r"(\w+) not (\w+);", p.facts)
        assert (npers, nitem) in neg, f"{p.pid}: premise does not flip the negative clue"
        dom = re.search(r"domain ([\w/]+) among ([\w/]+)", p.facts)
        items, people = dom.group(1).split("/"), dom.group(2).split("/")
        qi = p.ask.split("with the ")[1]
        assert solve_assign(people, items, pos + [(npers, nitem)], [], qi) == p.drift, \
            f"{p.pid}: drift mismatch"


# ── 4. the validators re-prove, and refuse tampering ─────────────────────────────────

def test_validators_pass_the_generated_sets():
    assert validate_logic(LOGIC) is True
    assert validate_assign(ASSIGN) is True


def test_validate_logic_raises_on_tampered_answer():
    # swap the correct token for another option: the re-proof from facts must fail
    p = LOGIC[0]
    other = next(o for o in p.options if o not in (p.correct, p.drift))
    with pytest.raises(AssertionError):
        validate_logic([replace(p, correct=other)])


def test_validate_assign_raises_on_tampered_answer():
    p = ASSIGN[0]
    other = next(o for o in p.options if o not in (p.correct, p.drift))
    with pytest.raises(AssertionError):
        validate_assign([replace(p, correct=other)])


# ── 5. the pool: 8 canonical + 12 ordering + 12 assignment = 32 ──────────────────────

def test_logic_pool_is_canonical_plus_expansion():
    pool = logic_pool()
    assert len(pool) == 32
    assert pool[:8] == CANONICAL_LOGIC
    assert pool[8:20] == LOGIC
    assert pool[20:] == ASSIGN
    pids = [p.pid for p in pool]
    assert len(pids) == len(set(pids)), "pool pids collide"
    for p in pool:
        assert p.kind == "text"
        assert 3 <= len(p.options) <= 5, f"{p.pid}: k off the 3–5 chance-floor range"
