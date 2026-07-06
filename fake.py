"""fake.py — the deterministic fake model behind the anti-rig suite (M0 task 3).

A mirror of the author's `DryRunLLM` (reclaim-eval src/reclaim/llm.py), re-implemented
here (D1: their package is never imported). The load-bearing property, theirs verbatim in
spirit and mechanism: **the fake reclaims only when the source's line-item tokens are
present in its context** — the same 18-char token test the per-trial gate uses — so a
passing validator run cannot be produced by a pattern-matching model that "just knows"
the answer. What the checks prove on this fake:

  1. the planted premise drifts it (every non-correction turn commits the wrong total);
  2. the reclaim window favors the DIRECTED arm (higher base rate, slower decay with
     commitment depth);
  3. the central anti-rig check: with the source absent from the carried note, reclaim
     fails for BOTH arms (a rare 5% "lucky" recovery keeps the check honest about noise).

Deliberate mirror details that matter downstream:
  - the no-source reply is their exact hedged shape ("I am not sure I have enough to
    recompute. ANSWER: <v>") — which our grader, mirroring their `_is_abstain`, reads as
    an ABSTENTION when wrong. Their probe notes the DryRun does NOT model the real
    emit-vs-abstain disposition split; neither does ours. The fake validates reclaim
    mechanics; the disposition probe needs real models (M0 tasks 6–7).
  - a correction turn is recognized by "recheck"/"wrong" in the last user message, and
    the directed arm by the first 8 chars of the locus appearing in it — both theirs.

Known limitation of the string test (theirs too, discovered the hard way): the marker is
the first 18 chars of the FACTS string ("tiles at $6 each ("), but most canonical
QUESTIONS phrase prices differently ("Tiles cost $6 each") — so on full-transcript cells
the fake sees the source as absent for 7 of the 8 canonical problems (notebooks' question
happens to say "at" and matches). Their own comment claims the marker "also appears
verbatim in the original question"; that holds only for their first problem, and their
probe runs this check on notes (where the facts string IS verbatim), not transcripts.
Ours does the same; the one marker-matching transcript is used to test depth decay.
Real models are unaffected — they recompute from the question's numbers, not our marker.

Second known limitation (found live on the first paid trials, 2026-07-06): the fake
answers "ANSWER: {drift}" in DOLLARS on every non-correction turn, including the
"express it in cents" follow-up — so it can never catch a unit-transform scoring bug.
That is exactly how a take test reading the LAST reply passed the validator suite and
then mis-scored real models (see runner.COMMIT_FOLLOWUP); test_m0's CentsAwareFake
covers that hole now.

Seeded and deterministic given (problem, seed): the validator suite's outcomes are
reproducible, never flaky.
"""
from __future__ import annotations

import random

from notes import SRC_MARKER
from problems import Problem

LUCKY = 0.05          # no-source "lucky recovery" rate, theirs
BASE = {"directed": 0.95, "generic": 0.85}    # reclaim base rates with source present
DECAY = {"directed": 0.06, "generic": 0.14}   # per-depth decay ("generic forgets faster")
FLOOR = 0.02


class DriftFake:
    """One fake per (problem, seed). Interface: .chat(messages) -> str, same as the
    real adapters, so the whole pipeline runs unchanged on it."""

    def __init__(self, problem: Problem, seed: int = 0):
        self.problem = problem
        self._rng = random.Random(seed)
        self.calls = 0

    # ── the source-token test the whole anti-rig property hangs on ──────────────────
    def _facts_present(self, messages) -> bool:
        marker = self.problem.facts[:SRC_MARKER].lower()
        return any(marker in (m.get("content") or "").lower() for m in messages)

    @staticmethod
    def _depth_hint(messages) -> int:
        # assistant turns so far = how deep the commitment ran (theirs)
        return sum(1 for m in messages if m["role"] == "assistant")

    def chat(self, messages) -> str:
        self.calls += 1
        last = (messages[-1].get("content") or "").lower()
        drift, correct = self.problem.drift, self.problem.correct
        # correction turn? simulate the reclaim window
        if "recheck" in last or "wrong" in last:
            # the broken sky: no recomputable source in context -> neither arm can
            # reclaim, no matter how directed (rare lucky recovery aside)
            if not self._facts_present(messages):
                val = correct if self._rng.random() < LUCKY else drift
                return f"I am not sure I have enough to recompute. ANSWER: {val}"
            arm = "directed" if self.problem.locus.lower()[:8] in last else "generic"
            p = max(FLOOR, BASE[arm] - DECAY[arm] * self._depth_hint(messages))
            val = correct if self._rng.random() < p else drift
            return f"Rechecking... ANSWER: {val}"
        # normal/drift turn: commit to the wrong answer
        return f"Using what was given, ANSWER: {drift}"
