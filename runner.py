"""runner.py — the two-session frames and the per-trial source gate (M0 task 3).

All prompt strings are re-typed VERBATIM from the author's reclaim-eval
`src/reclaim/experiment.py` (D6; read as reference per D1, never imported):
the SYSTEM prompt, the session-1 plant message, and the cross-session correction
(`reclaim_cross`) in both arms. v1's paid cells run the DIRECTED arm only (D2); the
generic arm is kept because the anti-rig suite needs it (validator #2: the window must
favor the directed arm on the deterministic fake).

The two sessions, concretely:
  session 1 (drift induction) — [system, user(plant)] then the model answers, then each
    commitment follow-up turn gets an answer, out to DEPTH turns. The plant injects the
    wrong premise; the follow-ups build on the running total without re-deriving the
    corrupted component. Their cross-session experiment fixes commitment at depth 8
    (`states[max(DEPTHS)]`), so DEPTH = 8 here. The drift-take test grades a
    dedicated measurement turn (`take_probe`, D11) that is never carried — see
    TAKE_PROBE below for why no existing turn can be read strictly.
  session 2 (the reclaim attempt) — a FRESH conversation: [system, user(note),
    user(directed correction)]. The note travels as a user turn, and the only inheritance
    from session 1 is that note. Special case, theirs verbatim: at g ≥ 0.99 under the
    lossy policy the FULL session-1 transcript survives instead of a note.

The source gate (`verify_note_gate`): before any session-2 call, the note is checked
mechanically against what its policy × g cell is SUPPOSED to carry — a lossy wall note
must demonstrably lack the source (their 18-char token test), a source_first note must
carry it. A mismatch raises SourceGateError and the trial never runs: a note only counts
as lossy if the source is provably absent, every trial, before any token is spent.

The `llm` argument everywhere is anything with `.chat(messages) -> str` — the
deterministic fake (fake.py) for the validator suite, a real OpenRouter adapter for the
pilots (built with m0.py).
"""
from __future__ import annotations

from notes import (build_sized_note, item_clauses, memory_note, retained_fraction,
                   source_present)
from problems import FOLLOWUPS, FOLLOWUPS_BY_KIND, Problem

# their SYSTEM prompt, verbatim (experiment.py)
SYSTEM = ("You are a careful assistant. Work the problem step by step. End every "
          "reply with a line 'ANSWER: <answer>'.")

# v1 fixes ONE commitment depth: the paper's cross-session runs use the deepest
# checkpoint (8 follow-ups after the plant)
DEPTH = 8

ARMS = ("directed", "generic")   # paid v1 cells: directed only; generic is validator-only


class SourceGateError(RuntimeError):
    """A note's source-presence contradicts its policy × g cell — the trial must not run."""


def plant(problem: Problem) -> str:
    """Opening user turn that injects the wrong premise to induce drift (verbatim)."""
    return (f"{problem.question}\nNote: {problem.wrong_premise}. Use that and "
            f"give {problem.ask}.")


def reclaim_cross(problem: Problem, arm: str = "directed") -> str:
    """The cross-session correction, both arms verbatim. The directed arm names the
    error locus in the trace's own terms WITHOUT giving the answer."""
    if arm == "generic":
        return (f"Looking back at that earlier conclusion, I think there is a mistake. "
                f"Please recheck and give the corrected {problem.ask} as 'ANSWER: <answer>'.")
    if arm == "directed":
        return (f"Looking back at that earlier conclusion, I think {problem.locus} was "
                f"wrong. Please recheck that and give the corrected {problem.ask} as "
                f"'ANSWER: <answer>'.")
    raise ValueError(f"unknown arm: {arm!r} (expected one of {ARMS})")


def build_trajectory(llm, problem: Problem, depth: int = DEPTH) -> list[dict]:
    """Session 1: plant drift, then commit over `depth` follow-up turns. Returns the
    full message list (ending on the model's last answer). The drift-take test reads
    the LAST assistant message: did it commit the planted wrong value? The task family
    picks its commitment turns (their FOLLOWUPS_BY_KIND idiom): arithmetic follow-ups
    for a number problem, the re-affirm-without-re-solving turns for a text one."""
    followups = FOLLOWUPS_BY_KIND[problem.kind]
    if not 0 <= depth <= len(followups):
        raise ValueError(f"depth must be 0..{len(followups)}, got {depth}")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": plant(problem)}]
    messages.append({"role": "assistant", "content": llm.chat(messages)})
    for fu in followups[:depth]:
        messages = messages + [{"role": "user", "content": fu}]
        messages.append({"role": "assistant", "content": llm.chat(messages)})
    return messages


def last_answer(trajectory: list[dict]) -> str:
    """The model's final session-1 reply."""
    assert trajectory and trajectory[-1]["role"] == "assistant"
    return trajectory[-1]["content"]


# The drift-take readout (D11, 2026-07-06). Take-conditioning is OUR addition (D8;
# the author's runner never checks drift), and the existing session-1 turns fail the
# readout two mechanical ways, both found live on the first paid trials: FOLLOWUPS[7]
# answers in CENTS (wrong units for a value test against problem.drift), and weaker
# models drop the ANSWER format on precisely the dollar-restatement turns (llama
# commits the drift in prose there — a strict parse under-counts take). The fix is
# the author's own idiom — their correction turn demands the format inline — applied
# to a dedicated measurement turn.
TAKE_PROBE = ("For the record, state the pre-tax total you have been using, as "
              "'ANSWER: <answer>'.")

# the logic take probe (D11 adapted for M4): the author's restatement question
# (FOLLOWUPS_LOGIC[6]) made FORMAT-EXPLICIT. Without the "as 'ANSWER: <word>'" demand a
# model answering literally with a bare token ("Tom") slips the strict ANSWER: parser and
# its real drift-take reads as took=false — the M4 pilot caught llama doing exactly this
# (10/20 bare-token drift commits scored 0). Graded by grader.took_logic, strict as ever.
TAKE_PROBE_LOGIC = ("What single word should I write down as the answer? "
                    "State it as 'ANSWER: <word>'.")


def take_probe(llm, trajectory: list[dict], problem: Problem | None = None) -> str:
    """One extra call: put the take-probe question to the (unmodified) session-1
    state and return the reply for grading. Measurement-only — the probe turn is
    NEVER carried, so session 2 inherits the depth-8 state exactly as their
    states[max(DEPTHS)] defines it. Pass the problem to pick the text-task probe;
    the no-problem call stays the arithmetic default (m0/m1 call it that way)."""
    probe = (TAKE_PROBE_LOGIC if problem is not None and problem.kind == "text"
             else TAKE_PROBE)
    return llm.chat(trajectory + [{"role": "user", "content": probe}])


def expected_source_presence(policy: str, integrity: float) -> bool:
    """What the policy × g cell is SUPPOSED to carry (the g-threshold mapping in
    notes.py): source_first keeps the source at every g; lossy/lossy_padded keep it
    only at g ≥ 0.5; blank never carries it."""
    if policy == "source_first":
        return True
    if policy in ("lossy", "lossy_padded"):
        return integrity >= 0.5
    if policy == "blank":
        return False
    raise ValueError(f"unknown policy: {policy!r}")


def verify_note_gate(note: str, problem: Problem, policy: str, integrity: float) -> None:
    """The per-trial source gate. Raises SourceGateError on any mismatch between what
    the note demonstrably carries (the 18-char token test) and what its cell claims."""
    expected = expected_source_presence(policy, integrity)
    actual = source_present(note, problem)
    if actual != expected:
        raise SourceGateError(
            f"{problem.pid}: {policy}@g={integrity} note has source_present={actual}, "
            f"cell requires {expected} — refusing to run this trial")


def session2_base(problem: Problem, policy: str, integrity: float,
                  transcript: list[dict] | None = None) -> list[dict]:
    """The session-2 context BEFORE the correction turn. Note-based for every cell
    except their verbatim special case: g ≥ 0.99 under lossy carries the full session-1
    transcript. Every note passes the source gate; the transcript case is gated on the
    original question (which carries the source) being present in it."""
    if policy == "lossy" and integrity >= 0.99:
        if not transcript:
            raise ValueError("g>=0.99 lossy carries the full transcript: pass one")
        if not any(problem.question in m.get("content", "") for m in transcript):
            raise SourceGateError(
                f"{problem.pid}: transcript cell is missing the original question")
        return list(transcript)
    note = memory_note(problem, integrity, policy)
    verify_note_gate(note, problem, policy, integrity)
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": note}]


def run_session2(llm, problem: Problem, policy: str, integrity: float,
                 arm: str = "directed", transcript: list[dict] | None = None) -> str:
    """One session-2 reclaim attempt: assemble the frame, gate the note, ask, return
    the raw reply (grading is grader.py's job — the runner never scores)."""
    msgs = session2_base(problem, policy, integrity, transcript)
    msgs = msgs + [{"role": "user", "content": reclaim_cross(problem, arm)}]
    return llm.chat(msgs)


# ── M5 (source-size boundary arm, D28-B): the budget×N session-2 frame + graded gate ──

def verify_size_gate(note: str, problem: Problem, policy: str, k_kept: int) -> None:
    """The GRADED per-trial source gate (M5). Raises SourceGateError unless the note's
    measured retained-source fraction matches what its cell built — a source_first note
    that fit `k_kept` of N line items must demonstrably carry exactly those, a
    lossy_padded note zero. Every trial, before any token is spent."""
    n_items = len(item_clauses(problem.facts))
    expected = (k_kept / n_items) if policy == "source_first" else 0.0
    actual = retained_fraction(note, problem)
    if abs(actual - expected) > 1e-9:
        raise SourceGateError(
            f"{problem.pid}: {policy} k_kept={k_kept} note has retained_fraction="
            f"{actual:.4f}, cell requires {expected:.4f} — refusing to run this trial")


def run_session2_budget(llm, problem: Problem, budget: int, policy: str,
                        arm: str = "directed") -> tuple[str, str, int]:
    """One M5 reclaim attempt at a fixed character budget (D28-B): build the budget-fit
    note (source_first keeps the k whole items that fit; lossy_padded is budget-matched),
    verify the graded gate, ask [system, note, directed correction]. Returns
    (reply, note, k) — k (items kept) is logged so the judge can split full-source (k=N)
    from partial (k<N), the paper's mechanism variable. The note is a write-time transform
    of the trajectory's problem, so one N-bank feeds both budgets and both policies (D5
    pairing)."""
    note, k = build_sized_note(problem, budget, policy)
    verify_size_gate(note, problem, policy, k)
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": note},
            {"role": "user", "content": reclaim_cross(problem, arm)}]
    return llm.chat(msgs), note, k
