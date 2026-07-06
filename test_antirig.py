"""test_antirig.py — the three anti-rig validator checks, on the deterministic fake.
No network, no model, $0. **This suite is the hard gate: no paid call runs until it is
green** (M0 brief, free-before-paid).

The fake (fake.py) reclaims ONLY when the source's line-item tokens are in its context,
so these checks cannot be passed by a model that pattern-matches its way to the right
answer — the paper's own validator design (theirs passes 3/3; ours must too):

  check 1 — the planted premise actually drifts the model;
  check 2 — the reclaim window favors the directed arm;
  check 3 — with the source absent from the note, reclaim fails for BOTH arms
            (and, contrast, source_first at the same wall g reclaims).

Every trial is seeded → the whole suite is deterministic, never flaky. Known limitation,
theirs too: the fake's wrong no-source replies are hedged, so they grade as ABSTAIN —
the fake validates reclaim mechanics, not the emit-vs-abstain disposition split (that is
exactly what M0's paid disposition probe measures on real models).
"""
from __future__ import annotations

import random

from fake import DriftFake
from grader import ABSTAIN, RECLAIMED, grade, took
from problems import CANONICAL, generate
from runner import build_trajectory, last_answer, run_session2
from stats import excludes_zero, newcombe_diff

WALL_G = 0.1


def _rr(policy: str, arm: str, n_per_problem: int, seed_base: int,
        integrity: float = WALL_G) -> tuple[int, int]:
    """Reclaim count over the canonical battery: n_per_problem seeded trials per
    problem, fresh fake each trial. Returns (k_reclaimed, n)."""
    k = n = 0
    for pi, p in enumerate(CANONICAL):
        for t in range(n_per_problem):
            llm = DriftFake(p, seed=seed_base + 1000 * pi + t)
            reply = run_session2(llm, p, policy, integrity, arm=arm)
            k += grade(reply, p).outcome == RECLAIMED
            n += 1
    return k, n


# ── check 1: the planted premise drifts the model ───────────────────────────────────
def test_check1_drift_takes():
    for p in CANONICAL:
        traj = build_trajectory(DriftFake(p, seed=0), p)
        assert took(last_answer(traj), p), f"{p.pid}: no drift take"
    # and on fresh generated instances (D5's trial diet)
    rng = random.Random(99)
    for i in range(5):
        p = generate(rng, pid=f"ar-{i}")
        traj = build_trajectory(DriftFake(p, seed=i), p)
        assert took(last_answer(traj), p), f"{p.pid}: no drift take"


# ── check 2: the window favors the directed arm ─────────────────────────────────────
def test_check2_directed_window_on_notes():
    # both arms on source-PRESENT notes (source_first at the wall) — the context their
    # own probe uses for this check: the facts string appears verbatim in the note, so
    # the fake sees the source. Same per-trial seed across arms = a paired comparison
    # (one uniform draw decides both arms), so the generic arm can never win a trial
    # the directed arm loses.
    k = {"directed": 0, "generic": 0}
    n_per = 30
    for pi, p in enumerate(CANONICAL):
        for t in range(n_per):
            for arm in ("directed", "generic"):
                llm = DriftFake(p, seed=7000 + 1000 * pi + t)
                reply = run_session2(llm, p, "source_first", WALL_G, arm=arm)
                k[arm] += grade(reply, p).outcome == RECLAIMED
    n = len(CANONICAL) * n_per   # 240 per arm
    d, lo, hi = newcombe_diff(k["generic"], n, k["directed"], n)
    assert excludes_zero(lo, hi) and d > 0.05, \
        f"window does not favor directed: directed {k['directed']}/{n} vs generic {k['generic']}/{n}"


def test_check2_window_decays_with_depth():
    # the depth half of the window, on the one cell where the fake can see the source
    # inside a TRANSCRIPT: notebooks' question happens to phrase prices as "at $4 each",
    # matching its facts marker. (For the other 7 canonical problems the questions say
    # "cost"/"are", so the fake's 18-char marker test reads their transcripts as
    # source-absent — a limitation of the FAKE's string test, documented in fake.py,
    # not of the runner: real models recompute from the question's numbers regardless
    # of phrasing.) At 9 assistant turns of commitment the fake's window is ~0.41
    # directed vs the 0.02 floor for generic.
    p = CANONICAL[0]                       # notebooks
    traj = build_trajectory(DriftFake(p, seed=0), p)
    k = {"directed": 0, "generic": 0}
    n = 40
    for t in range(n):
        for arm in ("directed", "generic"):
            llm = DriftFake(p, seed=31000 + t)
            reply = run_session2(llm, p, "lossy", 1.0, arm=arm, transcript=traj)
            k[arm] += grade(reply, p).outcome == RECLAIMED
    d, lo, hi = newcombe_diff(k["generic"], n, k["directed"], n)
    assert excludes_zero(lo, hi) and d > 0.2, \
        f"depth window absent: directed {k['directed']}/{n} vs generic {k['generic']}/{n}"


# ── check 3: source absent -> reclaim fails for BOTH arms ───────────────────────────
def test_check3_no_source_no_reclaim():
    n_per = 8   # x8 canonical problems = 64 trials per policy x arm
    for policy in ("lossy", "blank"):        # the two source-free wall notes
        for arm in ("directed", "generic"):
            k, n = _rr(policy, arm, n_per, seed_base=100)
            # the fake's 5% lucky-recovery keeps this honest about noise: near zero,
            # never exactly zero by fiat
            assert k / n <= 0.15, f"{policy}/{arm}: RR {k}/{n} — reclaim without source"


def test_check3_contrast_source_first_reclaims():
    k_sf, n = _rr("source_first", "directed", 8, seed_base=300)
    assert k_sf / n >= 0.85, f"source_first RR only {k_sf}/{n} with source present"
    # the wall itself, on the fake: source_first vs lossy at g=0.1, directed
    k_lossy, _ = _rr("lossy", "directed", 8, seed_base=100)
    d, lo, hi = newcombe_diff(k_lossy, n, k_sf, n)
    assert excludes_zero(lo, hi) and d > 0.5


def test_fake_disposition_limitation_documented():
    # the fake's wrong no-source replies are hedged -> ABSTAIN, so it cannot power an
    # emission-gap check; pin that so nobody mistakes fake abstentions for the real
    # disposition split the paid probe measures
    p = CANONICAL[0]
    llm = DriftFake(p, seed=11)   # a seed whose no-source draw misses the 5% lucky path
    reply = run_session2(llm, p, "lossy", WALL_G, arm="directed")
    g = grade(reply, p)
    assert g.outcome == ABSTAIN and g.hedged and g.parsed == p.drift
