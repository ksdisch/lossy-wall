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
    """The carried conclusion as their templates format it: the DRIFT total (the wrong
    value the model committed to in session 1), as money."""
    return f"${problem.drift:g}"


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


def source_present(note: str, problem: Problem) -> bool:
    """The per-trial source gate: is the recomputable source demonstrably in the note?
    Their exact mechanism — the first SRC_MARKER chars of the facts string, lowercased
    substring test. Run on EVERY trial's note before it counts as its policy (a note
    only counts as lossy if this returns False)."""
    return problem.facts[:SRC_MARKER].lower() in (note or "").lower()


def conclusion_present(note: str, problem: Problem) -> bool:
    """Is the stale committed value carried in the note? (Their classify_note test:
    the formatted conclusion string, lowercased substring.) Source gone + conclusion
    carried is the silent-failure regime the title claim lives on."""
    return _concl(problem).lower() in (note or "").lower()
