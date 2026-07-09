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
from collections import Counter

from fake import DriftFake, SourceSizeFake
from grader import (ABST, ABSTAIN, INHERIT, NOVEL, RECLAIMED, RECOV, classify_logic,
                    grade, took, took_logic)
from grader import EMIT_ATTRACTOR
from problems import CANONICAL, CANONICAL_LOGIC, generate, generate_sized
from problems_gen import logic_pool
from notes import build_sized_note, memory_note_sized
from runner import build_trajectory, last_answer, run_session2, run_session2_budget
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


# ── the logic family (M4): the same three checks on the text readout ─────────────────
# The fake is task-blind by construction — its source test is the facts marker, its
# replies are "ANSWER: {drift}" / "ANSWER: {val}", its arm detection is the locus
# prefix — so the identical mechanics must validate the logic pipeline end to end:
# reclaim (= RECOV) only when the clue tokens are in context. No paid logic call runs
# until this section is green (M4 brief, free-before-paid; the D24 pilot waits on it).

def _rr_logic(policy: str, arm: str, n_per_problem: int, seed_base: int,
              integrity: float = WALL_G) -> tuple[int, int]:
    """RECOV count over the canonical logic battery, seeded like _rr."""
    k = n = 0
    for pi, p in enumerate(CANONICAL_LOGIC):
        for t in range(n_per_problem):
            llm = DriftFake(p, seed=seed_base + 1000 * pi + t)
            reply = run_session2(llm, p, policy, integrity, arm=arm)
            k += classify_logic(reply, p) == RECOV
            n += 1
    return k, n


def test_logic_check1_drift_takes():
    # the planted clue drifts the fake on every logic problem the M4 bank can draw:
    # the 8 canonical and all 24 generated (took_logic reads the committed drift token)
    for p in logic_pool():
        traj = build_trajectory(DriftFake(p, seed=0), p)
        assert took_logic(last_answer(traj), p), f"{p.pid}: no drift take"


def test_logic_check2_directed_window_on_notes():
    # both arms on source-PRESENT logic notes (source_first at the wall); paired seeds
    # across arms as in the arithmetic check, so generic can never win a trial the
    # directed arm loses
    k = {"directed": 0, "generic": 0}
    n_per = 30
    for pi, p in enumerate(CANONICAL_LOGIC):
        for t in range(n_per):
            for arm in ("directed", "generic"):
                llm = DriftFake(p, seed=47000 + 1000 * pi + t)
                reply = run_session2(llm, p, "source_first", WALL_G, arm=arm)
                k[arm] += classify_logic(reply, p) == RECOV
    n = len(CANONICAL_LOGIC) * n_per   # 240 per arm
    d, lo, hi = newcombe_diff(k["generic"], n, k["directed"], n)
    assert excludes_zero(lo, hi) and d > 0.05, \
        f"window does not favor directed: directed {k['directed']}/{n} vs generic {k['generic']}/{n}"


def test_logic_check3_no_source_no_reclaim():
    n_per = 8   # x8 canonical logic problems = 64 trials per policy x arm
    for policy in ("lossy", "blank"):        # the two source-free wall notes
        for arm in ("directed", "generic"):
            k, n = _rr_logic(policy, arm, n_per, seed_base=52000)
            assert k / n <= 0.15, f"{policy}/{arm}: RR {k}/{n} — reclaim without source"


def test_logic_check3_contrast_source_first_reclaims():
    k_sf, n = _rr_logic("source_first", "directed", 8, seed_base=53000)
    assert k_sf / n >= 0.85, f"source_first RR only {k_sf}/{n} with clues present"
    # the wall itself, on the fake: source_first vs lossy at g=0.1, directed
    k_lossy, _ = _rr_logic("lossy", "directed", 8, seed_base=52000)
    d, lo, hi = newcombe_diff(k_lossy, n, k_sf, n)
    assert excludes_zero(lo, hi) and d > 0.5


def test_logic_fake_wall_reads_inherit_never_abst():
    # the fake's no-source reply hedges in prose but still COMMITS a token on its
    # ANSWER line — and the author's classify reads a committed token as a commit,
    # hedged or not (no hedge override in logic_failmode.py). So the fake's lossy wall
    # is INHERIT-heavy with zero ABST: reclaim mechanics only. Pin it so nobody
    # mistakes fake inherit/abst fractions for the real disposition split the D24
    # pilot's taxonomy read measures on real models. (Contrast: the arithmetic grade()
    # reads the same hedged reply as ABSTAIN — the two readouts differ by design,
    # each re-typed from the author's own instrument for that family.)
    p = CANONICAL_LOGIC[0]   # roles
    counts = Counter()
    for t in range(40):
        llm = DriftFake(p, seed=61000 + t)
        counts[classify_logic(run_session2(llm, p, "lossy", WALL_G, arm="directed"), p)] += 1
    assert counts[ABST] == 0 and counts[NOVEL] == 0
    assert counts[INHERIT] >= 30                 # the drift token, committed
    assert counts[RECOV] <= 6                    # the 5% lucky path, generously bounded


# ── the source-size family (M5, D28-B): the graded gate can't be gamed by partial source
# SourceSizeFake IS the author's bench_sizesweep.SizeFake, re-typed: it reclaims only when
# EVERY line-item clause is present (an exact sum needs all N), and past the cliff it emits
# the DRIFT (silent mis-sum), not an abstention. So a budget-STARVED source_first note (some
# items shed) fails to reclaim exactly like a source-free one, and does so worse-than-empty.
# The three checks: drift takes; full source reclaims while starved/partial source does not;
# and the past-cliff failure is a confident mis-sum. Deterministic (a validator). No paid M5
# call runs until this section is green (M5 brief, free-before-paid).

def _m5_battery(n: int = 8, k_items: int = 8):
    """A fresh battery of N-item receipts (seeded → deterministic)."""
    rng = random.Random(2025)
    return [generate_sized(rng, f"m5t-{i}", k_items=k_items) for i in range(n)]


def _sf_rr(battery, budget: int, policy: str = "source_first") -> tuple[int, int]:
    """Reclaim count over the battery at a fixed character budget."""
    k = n = 0
    for p in battery:
        reply, _note, _kept = run_session2_budget(SourceSizeFake(p), p, budget, policy)
        k += grade(reply, p).outcome == RECLAIMED
        n += 1
    return k, n


def test_m5_check1_drift_takes():
    for p in _m5_battery():
        traj = build_trajectory(SourceSizeFake(p), p)
        assert took(last_answer(traj), p), f"{p.pid}: no drift take"


def test_m5_check2_full_source_reclaims_starved_does_not():
    # a budget that holds the whole 8-item source reclaims; a tiny budget (partial source)
    # and the budget-matched lossy_padded floor do NOT — the cliff, mechanized
    battery = _m5_battery(k_items=8)
    k_full, n = _sf_rr(battery, 100000, "source_first")     # every item fits
    assert k_full == n, f"full source did not reclaim: {k_full}/{n}"
    k_starved, _ = _sf_rr(battery, 150, "source_first")     # only a couple items fit
    assert k_starved == 0, f"partial source reclaimed: {k_starved}/{n}"
    k_pad, _ = _sf_rr(battery, 600, "lossy_padded")         # budget-matched, no source
    assert k_pad == 0


def test_m5_check3_silent_missum_past_the_cliff():
    # past its boundary source_first does not abstain — it confidently sums the PARTIAL
    # source to the stale value (EMIT_ATTRACTOR), the paper's worse-than-empty finding
    battery = _m5_battery(k_items=8)
    for p in battery:
        reply, _n, k = run_session2_budget(SourceSizeFake(p), p, 150, "source_first")
        assert k < 8
        assert grade(reply, p).outcome == EMIT_ATTRACTOR, \
            f"{p.pid}: starved source_first should silently mis-sum, got {grade(reply, p).outcome}"


def test_m5_check3_contrast_cliff_separates():
    battery = _m5_battery(k_items=8)
    k_full, n = _sf_rr(battery, 100000, "source_first")
    k_starved, _ = _sf_rr(battery, 150, "source_first")
    d, lo, hi = newcombe_diff(k_starved, n, k_full, n)
    assert excludes_zero(lo, hi) and d > 0.5
