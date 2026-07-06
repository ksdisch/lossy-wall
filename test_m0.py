"""test_m0.py — the M0 pilot driver's free-testable parts. No network, no cost.

What's pinned here, before any paid call:
  - the D8/D9 verdict tiers EXACTLY as recorded in DECISIONS.md (encoding them in code
    is what makes the triggers un-bendable after data arrives);
  - the OpenRouter adapter's request shape — temperature 0.0 / max_tokens 600 (D10,
    matching their llm.py), the usage-cost accounting, and that the per-model config
    (MODEL_EXTRA_BODY) survives the usage.include merge — against a stubbed client.chat;
  - both pilot loops end-to-end on deterministic fakes: JSONL files and row shapes,
    take counting, the probe's reuse of taken pilot trajectories, the session-1 top-up,
    the D8-trigger skip, and the pre-committed amber → 24/arm extension (D9).

The DriftFake always commits the planted drift in session 1 (take = n/n) and, at the
g=0.1 wall, answers with their hedged no-source shape — which grades as ABSTAIN — so the
fake's probe gap is 0 (null): the fake validates machinery, not disposition (its
documented limitation; the real probe needs real models).
"""
from __future__ import annotations

import json

import pytest

import m0
from fake import DriftFake
from m0 import (MAX_TOKENS, TEMPERATURE, OpenRouterModel, d8_verdict, d9_verdict,
                openrouter_factory, pilot_problem, run_pilot, run_probe)
from problems import Problem

FAKES = {"fakea": "fake/model-a", "fakeb": "fake/model-b"}


def fake_factory(seed: int = 42):
    return lambda slug, problem: DriftFake(problem, seed=seed)


# ── the pre-committed verdict tiers (DECISIONS.md D8/D10, D9) ────────────────────────

def test_d10_constants_match_their_harness():
    assert TEMPERATURE == 0.0
    assert MAX_TOKENS == 600


def test_d8_tiers_at_n20():
    assert d8_verdict(20, 20) == "green"
    assert d8_verdict(14, 20) == "green"      # >= 70%
    assert d8_verdict(13, 20) == "amber"
    assert d8_verdict(10, 20) == "amber"      # >= 50%
    assert d8_verdict(9, 20) == "trigger"
    assert d8_verdict(0, 20) == "trigger"


def test_d9_tiers_at_12_per_arm():
    assert d9_verdict(12, 12) == "green"
    assert d9_verdict(4, 12) == "green"       # >= n/3 (about 33 points)
    assert d9_verdict(3, 12) == "amber"       # 2-3: extend to 24/arm, pre-committed
    assert d9_verdict(2, 12) == "amber"
    assert d9_verdict(1, 12) == "null"        # <= n/12
    assert d9_verdict(0, 12) == "null"
    assert d9_verdict(-3, 12) == "null"       # blank emitting MORE than lossy is no gap


def test_d9_after_extension_has_no_amber():
    # after the pre-committed extension the same bars scale (8 and 2 at 24) and the
    # amber escape hatch is gone: below the green bar is an honest claim-3 null
    assert d9_verdict(8, 24, final=True) == "green"
    assert d9_verdict(7, 24, final=True) == "null"
    assert d9_verdict(3, 24, final=True) == "null"
    assert d9_verdict(2, 24, final=True) == "null"


# ── the problem schedule (D5: fresh per trial; paired across models) ─────────────────

def test_pilot_problem_is_deterministic_and_fresh_per_trial():
    a1, a2 = pilot_problem(0, 3), pilot_problem(0, 3)
    assert a1 == a2                                # same seed + trial -> same problem
    assert pilot_problem(0, 4) != a1               # next trial -> fresh problem
    assert pilot_problem(1, 3) != a1               # different seed -> different problem
    assert a1.pid == "gen0-03"


# ── the OpenRouter adapter (stubbed client.chat — no network) ────────────────────────

class _Resp:
    """The slice of an OpenAI SDK response the adapter reads."""

    def __init__(self, content, prompt=10, completion=2, cost=0.001):
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]
        self.usage = type("U", (), {"prompt_tokens": prompt, "completion_tokens": completion,
                                    "cost": cost})()


def test_adapter_request_shape_and_accounting(monkeypatch):
    seen = []

    def stub_chat(messages, *, model, **kwargs):
        seen.append((messages, model, kwargs))
        return _Resp("pong. ANSWER: 5")

    monkeypatch.setattr(m0, "chat", stub_chat)
    monkeypatch.setitem(m0.MODEL_EXTRA_BODY, "fake/model-a", {"reasoning": {"enabled": False}})

    llm = OpenRouterModel("fake/model-a")
    out = llm.chat([{"role": "user", "content": "hi"}])
    assert out == "pong. ANSWER: 5"

    _, model, kwargs = seen[0]
    assert model == "fake/model-a"
    assert kwargs["temperature"] == 0.0            # D10
    assert kwargs["max_tokens"] == 600             # theirs
    # usage.include merged WITHOUT clobbering the per-model reasoning config
    assert kwargs["extra_body"] == {"reasoning": {"enabled": False},
                                    "usage": {"include": True}}

    llm.chat([{"role": "user", "content": "again"}])
    assert llm.calls == 2
    assert llm.prompt_tokens == 20 and llm.completion_tokens == 4
    assert llm.cost == pytest.approx(0.002)


def test_adapter_retries_the_choices_none_quirk_once(monkeypatch):
    # Seen live on qwen72b (2026-07-06): OpenRouter can return HTTP 200 whose body is
    # {'error': ..., 'choices': None} for a transient provider error — the SDK doesn't
    # retry those. One bounded retry, then a loud failure, so a 200-trial arm neither
    # crashes on a blip nor silently loops.
    class _ErrResp:
        choices = None
        usage = None
        error = {"message": "Provider returned error", "code": 400}

    replies = [_ErrResp(), _Resp("pong. ANSWER: 5")]
    monkeypatch.setattr(m0, "chat", lambda messages, *, model, **kw: replies.pop(0))
    llm = OpenRouterModel("fake/model-a")
    assert llm.chat([{"role": "user", "content": "hi"}]) == "pong. ANSWER: 5"

    monkeypatch.setattr(m0, "chat", lambda messages, *, model, **kw: _ErrResp())
    with pytest.raises(RuntimeError, match="Provider returned error"):
        llm.chat([{"role": "user", "content": "hi"}])


def test_adapter_empty_reply_is_empty_string(monkeypatch):
    monkeypatch.setattr(m0, "chat", lambda messages, *, model, **kw: _Resp(None, cost=None))
    llm = OpenRouterModel("fake/model-a")
    assert llm.chat([{"role": "user", "content": "hi"}]) == ""
    assert llm.cost == 0.0                         # a missing cost never poisons the sum


def test_openrouter_factory_caches_one_adapter_per_slug():
    llm_for, cache = openrouter_factory()
    p1, p2 = pilot_problem(0, 0), pilot_problem(0, 1)
    a = llm_for("fake/model-a", p1)
    assert llm_for("fake/model-a", p2) is a        # per-model, not per-trial
    assert llm_for("fake/model-b", p1) is not a
    assert set(cache) == {"fake/model-a", "fake/model-b"}


# ── the drift-take pilot on the fake (task 6 machinery) ──────────────────────────────

def test_run_pilot_on_fake_counts_takes_and_writes_logs(tmp_path):
    res = run_pilot(fake_factory(), n=4, seed=0, runs_root=tmp_path, models=FAKES)

    for key in FAKES:
        arm = res[key]
        assert arm["slug"] == FAKES[key]
        assert (arm["n"], arm["takes"]) == (4, 4)  # the fake always commits the drift
        assert arm["verdict"] == "green"
        assert 0.0 <= arm["wilson_lo"] <= arm["wilson_hi"] <= 1.0

        arm_dir = tmp_path / f"pilot-{key}"
        rows = [json.loads(l) for l in (arm_dir / "results.jsonl").read_text().splitlines()]
        assert len(rows) == 4
        for i, row in enumerate(rows):
            assert row["trial"] == i and row["took"] is True
            p = Problem(**row["problem"])          # probe reconstructs problems from rows
            assert row["parsed"] == pytest.approx(p.drift)
            # full hand-readable trajectory: [system, plant, a] + 8 x (user, a) = 19 lines
            traj = (arm_dir / f"trial-{i:02d}.jsonl").read_text().splitlines()
            assert len(traj) == 19

    # paired design: every model saw the SAME fresh problem schedule
    pids = {key: [json.loads(l)["pid"]
                  for l in (tmp_path / f"pilot-{key}" / "results.jsonl").read_text().splitlines()]
            for key in FAKES}
    assert pids["fakea"] == pids["fakeb"]


class CentsAwareFake(DriftFake):
    """DriftFake that answers the cents follow-up IN CENTS, as real models do — the
    plain DriftFake answers dollars on every turn and so can never catch a
    unit-transform scoring bug (how the live take-test bug slipped the anti-rig net)."""

    def chat(self, messages) -> str:
        last = (messages[-1].get("content") or "").lower()
        if "in cents" in last:
            return f"ANSWER: {self.problem.drift * 100:g}"
        return super().chat(messages)


def test_run_pilot_take_test_survives_the_cents_turn(tmp_path):
    llm_for = lambda slug, problem: CentsAwareFake(problem, seed=1)  # noqa: E731
    res = run_pilot(llm_for, n=2, seed=0, runs_root=tmp_path,
                    models={"fakea": FAKES["fakea"]})
    assert res["fakea"]["takes"] == 2   # last reply is cents; the take probe decides


class FormatDropFake(DriftFake):
    """llama-style (seen live 2026-07-06): commits the drift in PROSE on the
    dollar-restatement turns — no ANSWER line — unless the turn demands the format
    inline, as the take-probe turn does."""

    def chat(self, messages) -> str:
        last = (messages[-1].get("content") or "")
        if "'ANSWER: <answer>'" in last:
            return f"For the record, ANSWER: {self.problem.drift:g}"
        if "restate" in last.lower() or "confirm" in last.lower():
            return f"The original pre-tax total was ${self.problem.drift:g}."
        return super().chat(messages)


def test_run_pilot_take_test_survives_format_dropping_models(tmp_path):
    llm_for = lambda slug, problem: FormatDropFake(problem, seed=1)  # noqa: E731
    res = run_pilot(llm_for, n=2, seed=0, runs_root=tmp_path,
                    models={"fakea": FAKES["fakea"]})
    assert res["fakea"]["takes"] == 2   # prose commitment still counts: the probe asks


# ── the disposition probe on the fake (task 7 machinery) ─────────────────────────────

def test_run_probe_reuses_takes_and_grades_the_wall(tmp_path):
    run_pilot(fake_factory(), n=4, seed=0, runs_root=tmp_path, models=FAKES)
    res = run_probe(fake_factory(), n_per_arm=3, seed=0, runs_root=tmp_path, models=FAKES)

    for key in FAKES:
        arm = res[key]
        assert arm["n_per_arm"] == 3 and not arm["short"] and not arm["extended"]
        # the fake's no-source reply is hedged -> ABSTAIN for both arms -> no gap
        assert arm["wrong"] == {"lossy": 0, "blank": 0}
        assert arm["gap"] == 0 and arm["verdict"] == "null"
        assert arm["d"] == pytest.approx(0.0)
        assert arm["newcombe_lo"] <= 0.0 <= arm["newcombe_hi"]

        rows = [json.loads(l)
                for l in (tmp_path / f"probe-{key}" / "results.jsonl").read_text().splitlines()]
        assert len(rows) == 6                      # 3 trials x 2 policies
        assert {r["policy"] for r in rows} == {"lossy", "blank"}
        for r in rows:
            assert r["g"] == 0.1
            assert "ANSWER:" in r["reply"]
            assert r["outcome"] in ("abstain", "reclaimed")   # never a wrong emission here
            assert "(Memory of an earlier session.)" in r["note"]


def test_run_probe_tops_up_session1_when_takes_run_short(tmp_path):
    run_pilot(fake_factory(), n=2, seed=0, runs_root=tmp_path, models=FAKES)
    res = run_probe(fake_factory(), n_per_arm=4, seed=0, runs_root=tmp_path, models=FAKES)
    for key in FAKES:
        arm = res[key]
        assert arm["n_per_arm"] == 4 and arm["topup_trials"] == 2 and not arm["short"]
        topups = (tmp_path / f"probe-{key}" / "topup.jsonl").read_text().splitlines()
        assert [json.loads(l)["trial"] for l in topups] == [2, 3]  # schedule continues


class NoTakeFake:
    """Session 1: answers an unplanted value (never takes). Session 2: emits it (wrong)."""

    def __init__(self, problem):
        self.problem = problem

    def chat(self, messages) -> str:
        return "ANSWER: 0"


def test_run_probe_skips_a_triggered_model(tmp_path):
    llm_for = lambda slug, problem: NoTakeFake(problem)          # noqa: E731
    pilot = run_pilot(llm_for, n=4, seed=0, runs_root=tmp_path, models=FAKES)
    assert all(pilot[k]["verdict"] == "trigger" for k in FAKES)  # 0/4 takes
    res = run_probe(llm_for, n_per_arm=3, seed=0, runs_root=tmp_path, models=FAKES)
    for key in FAKES:
        assert res[key]["skipped"]                 # no probe on a fired model
        assert not (tmp_path / f"probe-{key}").exists()


def test_run_probe_reports_short_honestly(tmp_path):
    # 2 pilot takes, top-ups never take -> probe must run at 2/arm and SAY so, not stall
    run_pilot(fake_factory(), n=2, seed=0, runs_root=tmp_path, models={"fakea": FAKES["fakea"]})
    llm_for = lambda slug, problem: NoTakeFake(problem)          # noqa: E731
    res = run_probe(llm_for, n_per_arm=4, seed=0, runs_root=tmp_path,
                    models={"fakea": FAKES["fakea"]})
    arm = res["fakea"]
    assert arm["short"] and arm["n_per_arm"] == 2
    # NoTakeFake's session-2 "ANSWER: 0" is an unhedged wrong value on BOTH arms
    assert arm["wrong"] == {"lossy": 2, "blank": 2} and arm["gap"] == 0


class CountingDispositionFake:
    """Take in session 1 always; at the wall, emit the attractor for the first
    `emit_first` LOSSY replies and abstain (hedged) otherwise — a hand-crank for the
    exact amber gap the D9 extension path needs."""

    def __init__(self, problem, state, emit_first):
        self.problem = problem
        self.state = state
        self.emit_first = emit_first

    def chat(self, messages) -> str:
        note = next((m["content"] for m in messages
                     if "(Memory of an earlier session.)" in (m.get("content") or "")), None)
        if note is None:                            # session 1: commit the drift
            return f"Using what was given, ANSWER: {self.problem.drift}"
        if "no figures" in note.lower():            # blank arm: always abstain
            return "I am not sure I can recompute. ANSWER: 0"
        if self.state["lossy_emits"] < self.emit_first:
            self.state["lossy_emits"] += 1
            return f"Rechecking... ANSWER: {self.problem.drift}"
        return "I am not sure I can recompute. ANSWER: 0"


def test_run_probe_amber_extends_to_24_per_arm(tmp_path):
    state = {"lossy_emits": 0}
    llm_for = lambda slug, problem: CountingDispositionFake(problem, state, 2)  # noqa: E731
    models = {"fakea": FAKES["fakea"]}
    run_pilot(llm_for, n=13, seed=0, runs_root=tmp_path, models=models)

    res = run_probe(llm_for, n_per_arm=12, seed=0, runs_root=tmp_path, models=models)
    arm = res["fakea"]
    # gap 2/12 -> amber -> the PRE-COMMITTED extension runs to 24/arm automatically,
    # topping up session-1 trajectories to fill the take pool (13 + 11 = 24)
    assert arm["extended"] and arm["n_per_arm"] == 24
    assert arm["topup_trials"] == 11
    assert arm["wrong"] == {"lossy": 2, "blank": 0} and arm["gap"] == 2
    assert arm["verdict"] == "null"                # 2 <= 24/12: below the scaled null bar
    rows = (tmp_path / "probe-fakea" / "results.jsonl").read_text().splitlines()
    assert len(rows) == 48                         # 24 trials x 2 policies, one row each
