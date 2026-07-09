"""notes.py — the four memory-note policies as pure functions (M0 task 2).

Every template is re-typed VERBATIM from the author's reclaim-eval
`src/reclaim/experiment.py::memory_note` (D6; read as protocol reference per D1, never
imported). A *pure function* here means: same problem + same g + same policy always
yields the exact same note string — no state, no randomness, no network — which is what
makes the note layer testable for free and the per-trial source gate meaningful.

The integrity knob g is a THRESHOLD mapping in their protocol (not a fractional
line-item shedding):

  lossy         g ≥ 0.5 : facts + planted premise + wrong conclusion
                0.2–0.5 : planted premise + wrong conclusion   (source gone — the wall)
                g < 0.2 : wrong conclusion only
  source_first  g ≥ 0.5 : facts + planted premise + conclusion ("you reached …")
                g < 0.5 : facts only, conclusion dropped ("the earlier answer may be off")
  lossy_padded  the lossy note at the same g, padded with PAD sentences to at least the
                length of the source_first note at that g (the budget-match control:
                any source_first advantage can't be "it had more text")
  blank         a fixed no-content note: neither source nor conclusion, only that an
                earlier session was determining `ask`

Two deliberate divergences from their code, both defensive:
  - their `memory_note` treats ANY unrecognized policy string as lossy (a silent
    fall-through default); ours raises ValueError — a typo'd policy name must crash,
    not quietly grade a lossy cell under the wrong label.
  - their fifth policy (`source_plus_conclusion`) is out of v1 scope (D2) — not ported.

Runner-level fact documented here, implemented in runner.py: their cross-session runner
special-cases g ≥ 0.99 under lossy to carry the FULL session-1 transcript instead of a
note (`run_problem_crosssession`); the note templates below cover every other cell.

The per-trial source-absence gate (`source_present`) mirrors their token test exactly
(probe.py SRC_MARKER / DryRunLLM._facts_present): the first 18 characters of the facts
string, lowercased substring match. The facts string appears verbatim in a source_first
note and in the original question, never in a wall-tight lossy note — so presence is a
measurable property of the emitted string, not an assumption.
"""
from __future__ import annotations

from problems import Problem

POLICIES: tuple[str, ...] = ("lossy", "lossy_padded", "source_first", "blank")

INTEGRITY: tuple[float, ...] = (1.0, 0.6, 0.3, 0.1)   # the v1 g grid (KICKOFF/D2)

# the padding sentence, verbatim (experiment.py PAD)
PAD = (" (For the record, this entry was retained from an archived session log; no "
       "additional working was preserved with it.)")

# how many leading chars of the facts string must survive for the source to count as
# present — their anti-rig token test, verbatim (probe.py SRC_MARKER)
SRC_MARKER = 18


def _concl(problem: Problem) -> str:
    """The carried conclusion as their templates format it, by answer kind (their
    kind-aware _concl, verbatim): the DRIFT value the model committed to in session 1 —
    as money for a number task, the bare token for a text task."""
    if problem.kind == "number":
        return f"${problem.drift:g}"
    return f"{problem.drift}"


def memory_note(problem: Problem, integrity: float, policy: str = "lossy") -> str:
    """The compressed carry-over memory at the given integrity, per policy (verbatim
    templates; see module docstring for the g mapping)."""
    concl = _concl(problem)
    facts = problem.facts
    ask = problem.ask
    if policy == "source_first":
        if integrity >= 0.5:
            return (f"(Memory of an earlier session.) The facts were: {facts}. A note "
                    f"said {problem.wrong_premise}. You reached {ask} of {concl}.")
        # tight budget: keep ONLY the source, drop the (re-derivable) conclusion
        return (f"(Memory of an earlier session.) The facts were: {facts}. You were "
                f"determining {ask}; the earlier answer may be off.")
    if policy == "lossy_padded":
        base = memory_note(problem, integrity, "lossy")
        target = len(memory_note(problem, integrity, "source_first"))
        while len(base) < target:
            base += PAD
        return base
    if policy == "blank":
        # keep NEITHER source nor conclusion: nothing to inherit, nothing to recompute from
        return (f"(Memory of an earlier session.) You were earlier determining {ask}. "
                f"No figures or details from that session were retained.")
    if policy == "lossy":
        if integrity >= 0.5:
            return (f"(Memory of an earlier session.) The facts were: {facts}. A note said "
                    f"{problem.wrong_premise}. You concluded {ask} was {concl}.")
        if integrity >= 0.2:
            return (f"(Memory of an earlier session.) You concluded that "
                    f"{problem.wrong_premise}, and that {ask} was {concl}.")
        return f"(Memory of an earlier session.) You concluded {ask} was {concl}."
    raise ValueError(f"unknown policy: {policy!r} (expected one of {POLICIES})")


# ── M5 (source-size boundary arm; opened 2026-07-09) ──────────────────────────────────
# OUR CONSTRUCTION (M5-BRIEF D28): the budget-capped source_first note and the graded
# source gate. The source_first FIX keeps the recomputable source and drops the
# re-derivable conclusion; M5 asks what happens when the source itself no longer fits the
# note budget. We realize the budget by the number of WHOLE line items it holds: at
# retained fraction s = n_keep / K the note carries the first n_keep of the receipt's K
# line-item clauses (the budget that fits exactly n_keep items), dropping the overflow.
# lossy is unchanged — the tiny wrong conclusion always fits, so it is the flat wall floor
# the cliff falls toward, identical at every s.


def item_clauses(facts: str) -> list[str]:
    """Split a K-item receipt's facts string into its line-item clauses — the units the
    budget sheds. The clause format (`"<good> at $<p> each (<q> bought)"` joined by
    " and ") carries no internal " and ", so the split is exact."""
    return [c.strip() for c in facts.split(" and ") if c.strip()]


def memory_note_sized(problem: Problem, policy: str, n_keep: int) -> str:
    """The M5 budget-capped memory note. `source_first` keeps the first `n_keep` whole
    line items (the budget that fits n_keep) and drops the conclusion (the wall variant of
    the fix — keep source, shed the re-derivable answer); `lossy` keeps only the wrong
    conclusion (always fits, so the same note at every budget). Pure: same inputs → same
    string."""
    clauses = item_clauses(problem.facts)
    if not 0 <= n_keep <= len(clauses):
        raise ValueError(f"n_keep must be 0..{len(clauses)}, got {n_keep}")
    if policy == "source_first":
        kept = " and ".join(clauses[:n_keep])
        return (f"(Memory of an earlier session.) The facts were: {kept}. You were "
                f"determining {problem.ask}; the earlier answer may be off.")
    if policy == "lossy":
        return (f"(Memory of an earlier session.) You concluded {problem.ask} was "
                f"{_concl(problem)}.")
    raise ValueError(f"unknown M5 policy: {policy!r} (expected 'lossy' or 'source_first')")


def retained_fraction(note: str, problem: Problem) -> float:
    """The GRADED per-trial source gate (M5's generalization of source_present from
    binary to a count): the fraction of the receipt's K line-item clauses demonstrably
    present in the note. Run on every trial — a source_first cell claiming s must carry
    exactly ⌊s·K⌋ line items; a lossy cell must carry zero. A mechanical property of the
    emitted string, never an assumption."""
    clauses = item_clauses(problem.facts)
    if not clauses:
        return 0.0
    low = (note or "").lower()
    present = sum(1 for c in clauses if c.lower() in low)
    return present / len(clauses)


def build_sized_note(problem: Problem, budget: int, policy: str) -> tuple[str, int]:
    """The paper's `sizesweep.build_note` (D28-B): fix a CHARACTER budget and fit the
    note to it. `source_first` greedily keeps whole line items in listed order while the
    note stays within `budget` chars (k items kept); `lossy_padded` is the wrong
    conclusion padded with neutral filler to the source_first note's length at that
    budget (the budget-matched floor — the paper's comparator: any source_first advantage
    can't be 'it had more text'). Returns (note, k). As N outgrows the budget, k < N and an
    exact sum needs all N, so source_first cliffs — the boundary M5 measures."""
    clauses = item_clauses(problem.facts)
    if policy == "source_first":
        k = 0
        for i in range(len(clauses) + 1):
            if len(memory_note_sized(problem, "source_first", i)) <= budget:
                k = i
            else:
                break
        return memory_note_sized(problem, "source_first", k), k
    if policy == "lossy_padded":
        target = len(build_sized_note(problem, budget, "source_first")[0])
        base = memory_note_sized(problem, "lossy", 0)   # the wrong conclusion, no source
        while len(base) < target:
            base += PAD
        return base, 0
    raise ValueError(f"unknown M5 budget policy: {policy!r} "
                     f"(expected 'source_first' or 'lossy_padded')")


def source_present(note: str, problem: Problem) -> bool:
    """The per-trial source gate: is the recomputable source demonstrably in the note?
    Their exact mechanism — the first SRC_MARKER chars of the facts string, lowercased
    substring test. Run on EVERY trial's note before it counts as its policy (a note
    only counts as lossy if this returns False)."""
    return problem.facts[:SRC_MARKER].lower() in (note or "").lower()


def conclusion_present(note: str, problem: Problem) -> bool:
    """Is the stale committed value carried in the note? (Their classify_note test:
    the formatted conclusion string, lowercased substring.) Source gone + conclusion
    carried is the silent-failure regime the title claim lives on.

    Text-task caveat: a bare drift TOKEN (a name like "Ben") can also appear inside the
    clue set itself, so on logic this test can read True on a note that carries only the
    source. It stays a number-task instrument; on logic the worse-than-empty read comes
    from the reply-side taxonomy (grader.classify_logic INHERIT), never from this."""
    return _concl(problem).lower() in (note or "").lower()
