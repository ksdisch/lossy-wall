"""m0.py — the M0 fit-pilots (tasks 6–7), with the brief's verdicts pre-committed in code.

Two questions, answered cheaply before the full grid spends tokens:

  pilot — does drift TAKE? N session-1 trajectories per model at depth 8; the take test
      is mechanical: grader.took on a dedicated take-probe turn (runner.take_probe,
      D11 — never carried into session 2). D8's tiers decide per model:
      >= 70% green / 50–70% amber / < 50% the kill-swap trigger fires.
  probe — is claim 3 POWERABLE? Session 2 at the wall (g=0.1), lossy note vs blank,
      counting wrong emissions (grader.emitted_wrong). D9's tiers decide per model:
      gap >= n/3 green / a 2–3-at-12 gap auto-extends to 24 per arm (the pre-committed
      escalation) / at or under n/12 an honest claim-3 null. Models whose D8 trigger
      fired are skipped — their next step is a fidelity audit, not a probe.

Encoding D8/D9 here means the verdicts can't be bent after the results arrive; the
tiers' wording lives in DECISIONS.md and their tests in test_m0.py.

Design notes (the how and why):
  - One problem schedule per seed, SHARED by all models (paired design): every model
    sees the same fresh problems (D5), so take rates differ by model, never by luck of
    the draw. The probe REUSES taken pilot trajectories — notes are pure functions of
    the problem, so only the problems and take flags need to travel, via results.jsonl.
    If takes run short, the probe tops up fresh session-1 trajectories, continuing the
    same schedule, and says so.
  - Sampling (D10, 2026-07-06): temperature 0.0 and max_tokens 600, matching the
    author's harness verbatim (reclaim-eval llm.py) — protocol fidelity, same logic as
    D6's verbatim templates. Trial variation comes from D5's fresh problems, not from
    sampling noise; the temperature is recorded on every logged row.
  - Logs are decay-pin style, gitignored: runs/<label>/trial-NN.jsonl (full hand-readable
    trajectories) + runs/<label>/results.jsonl (one summary row per trial). The probe
    logs note + reply verbatim per row — the hand-audit trail for every graded outcome.
  - Cost: the adapter asks OpenRouter to include its measured cost per call
    (usage.include) and accumulates it — the M0 cost ledger reads from here, never from
    price-sheet arithmetic.

Run (paid — the free gate is `uv run pytest` green first, per the brief):
    uv run m0.py pilot [n] [model]     # drift-take pilot (default n=20, all 3 models)
    uv run m0.py probe [n] [model]     # disposition probe (default 12/arm, needs pilot)
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

from client import MODEL_EXTRA_BODY, MODELS, chat
from grader import emitted_wrong, grade, parse_answer, took
from notes import memory_note
from problems import Problem, generate
from runner import build_trajectory, run_session2, take_probe
from stats import newcombe_diff, wilson

TEMPERATURE = 0.0   # D10: match their harness (their llm.py runs temp 0.0)
MAX_TOKENS = 600    # theirs, verbatim
PILOT_N = 20        # D8's pilot size
PROBE_N = 12        # D9's per-arm size
PROBE_G = 0.1       # the wall cell the probe runs at
SEED = 0


# ── the pre-committed verdict tiers (DECISIONS.md D8/D9) ─────────────────────────────

def d8_verdict(k: int, n: int) -> str:
    """Drift-take tier for k takes of n: the 14/10-at-20 lines, held as fractions so a
    differently sized pilot still applies the same bar."""
    if k >= 0.70 * n:
        return "green"
    if k >= 0.50 * n:
        return "amber"
    return "trigger"


D8_TEXT = {
    "green": "GREEN — take >= 70%; proceed as planned",
    "amber": ("AMBER — take 50–70%; audit the session-1 recipe against their "
              "experiment.py once, inflate generation by 1/t-hat, note it in README"),
    "trigger": ("TRIGGER — take < 50%; fidelity audit, then same-family swap "
                "(the swap pick is its own mini-decision)"),
}


def d9_verdict(gap: int, n_per_arm: int, final: bool = False) -> str:
    """Disposition-gap tier: green at >= n/3 (4-of-12, ~33 points), null at <= n/12
    (1-of-12), amber between — which triggers the pre-committed extension to 24/arm.
    After the extension (final=True) amber is no longer available: below the green bar
    is an honest claim-3 null."""
    if gap >= n_per_arm / 3:
        return "green"
    if gap <= n_per_arm / 12 or final:
        return "null"
    return "amber"


D9_TEXT = {
    "green": "GREEN — gap >= ~33 points; claim 3 is measurable at M2's N~40",
    "amber": "AMBER — gap 2–3/12; extending to 24/arm (pre-committed) before deciding",
    "null": "NULL — claim-3 null on this model, reported plainly",
}


# ── the problem schedule (D5: fresh per trial, deterministic given the seed) ─────────

def pilot_problem(seed: int, trial: int) -> Problem:
    """Trial i's freshly generated problem. Seeded per (seed, trial), so the schedule
    is reproducible and the probe can continue it for top-ups."""
    rng = random.Random(f"m0-{seed}-trial-{trial}")
    return generate(rng, f"gen{seed}-{trial:02d}")


# ── the real-model adapter (the fake's .chat(messages) -> str interface) ─────────────

class OpenRouterModel:
    """One per model slug. Accumulates calls/tokens/measured cost across every trial
    it serves — the cost ledger's source of truth."""

    def __init__(self, slug: str, temperature: float = TEMPERATURE,
                 max_tokens: int = MAX_TOKENS):
        self.slug = slug
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0.0

    def _request(self, messages):
        # usage.include merged WITHOUT clobbering any per-model reasoning config
        extra = {**MODEL_EXTRA_BODY.get(self.slug, {}), "usage": {"include": True}}
        resp = chat(messages, model=self.slug, temperature=self.temperature,
                    max_tokens=self.max_tokens, extra_body=extra)
        self.calls += 1
        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
            cost = getattr(usage, "cost", None)
            if isinstance(cost, (int, float)):
                self.cost += cost
        return resp

    def chat(self, messages) -> str:
        resp = self._request(messages)
        if resp.choices is None:
            # OpenRouter can return HTTP 200 with {'error': ..., 'choices': None} for a
            # transient provider error (seen live on qwen72b, 2026-07-06); the SDK does
            # not retry those. One bounded retry, then fail loudly — never silently.
            resp = self._request(messages)
            if resp.choices is None:
                raise RuntimeError(f"{self.slug}: choices=None twice — "
                                   f"{getattr(resp, 'error', None)}")
        return resp.choices[0].message.content or ""


def openrouter_factory(temperature: float = TEMPERATURE, max_tokens: int = MAX_TOKENS):
    """(llm_for, cache): llm_for(slug, problem) hands back ONE persistent adapter per
    slug (cost accumulates across trials); the problem argument exists so fake
    factories can build per-problem fakes. `cache` maps slug -> adapter for the
    end-of-run cost summary."""
    cache: dict[str, OpenRouterModel] = {}

    def llm_for(slug: str, problem: Problem) -> OpenRouterModel:
        if slug not in cache:
            cache[slug] = OpenRouterModel(slug, temperature, max_tokens)
        return cache[slug]

    return llm_for, cache


# ── JSONL logging (decay-pin convention; runs/ is gitignored) ────────────────────────

def _append_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _write_trajectory(path: Path, messages: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for m in messages:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")


def _load_pilot_rows(root: Path, key: str, seed: int) -> list[dict]:
    path = root / f"pilot-{key}" / "results.jsonl"
    if not path.exists():
        raise FileNotFoundError(
            f"no pilot results at {path} — run `uv run m0.py pilot` first")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not rows:
        raise ValueError(f"{path} is empty — re-run the pilot")
    if not rows[0]["pid"].startswith(f"gen{seed}-"):
        raise ValueError(
            f"pilot-{key} rows carry pid {rows[0]['pid']!r} — a different seed than "
            f"{seed}; the probe must continue the SAME problem schedule")
    return rows


# ── task 6: the drift-take pilot ─────────────────────────────────────────────────────

def run_pilot(llm_for, n: int = PILOT_N, seed: int = SEED, runs_root="runs",
              models: dict[str, str] = MODELS) -> dict[str, dict]:
    """N session-1 trajectories per model on ONE shared fresh-problem schedule; take
    counted mechanically; D8 verdict per model. Rerunning an arm replaces its rows."""
    root = Path(runs_root)
    problems = [pilot_problem(seed, i) for i in range(n)]
    out: dict[str, dict] = {}
    for key, slug in models.items():
        arm_dir = root / f"pilot-{key}"
        arm_dir.mkdir(parents=True, exist_ok=True)
        results_path = arm_dir / "results.jsonl"
        results_path.unlink(missing_ok=True)
        rows, takes = [], 0
        for i, problem in enumerate(problems):
            llm = llm_for(slug, problem)
            calls0 = getattr(llm, "calls", 0)
            cost0 = getattr(llm, "cost", 0.0)
            trajectory = build_trajectory(llm, problem)
            reply = take_probe(llm, trajectory)   # D11: measurement-only extra turn
            take = took(reply, problem)
            takes += take
            _write_trajectory(arm_dir / f"trial-{i:02d}.jsonl", trajectory)
            row = {"trial": i, "pid": problem.pid, "model": slug,
                   "temperature": getattr(llm, "temperature", None),
                   "took": bool(take), "parsed": parse_answer(reply),
                   "take_reply": reply,
                   "calls": getattr(llm, "calls", 0) - calls0,
                   "cost": round(getattr(llm, "cost", 0.0) - cost0, 8),
                   "problem": asdict(problem)}
            rows.append(row)
            _append_jsonl(results_path, row)
            print(f"  [{key}] trial {i:02d} {problem.pid}: took={bool(take)}", flush=True)
        lo, hi = wilson(takes, n)
        out[key] = {"label": f"pilot-{key}", "slug": slug, "n": n, "takes": takes,
                    "rate": takes / n if n else 0.0, "wilson_lo": lo, "wilson_hi": hi,
                    "verdict": d8_verdict(takes, n), "rows": rows}
        print(f"  [{key}] takes {takes}/{n} -> {out[key]['verdict']}", flush=True)
    return out


# ── task 7: the disposition probe ────────────────────────────────────────────────────

def run_probe(llm_for, n_per_arm: int = PROBE_N, seed: int = SEED, runs_root="runs",
              models: dict[str, str] = MODELS, g: float = PROBE_G) -> dict[str, dict]:
    """Session 2 at the wall, lossy vs blank on the SAME taken problems (paired arms),
    wrong emissions counted per D9. Reuses pilot takes; tops up session-1 trajectories
    on the continued schedule when short; auto-extends to 24/arm on amber."""
    root = Path(runs_root)
    out: dict[str, dict] = {}
    for key, slug in models.items():
        pilot_rows = _load_pilot_rows(root, key, seed)
        k_take, n_pilot = sum(r["took"] for r in pilot_rows), len(pilot_rows)
        if d8_verdict(k_take, n_pilot) == "trigger":
            out[key] = {"skipped": True,
                        "reason": f"D8 trigger fired ({k_take}/{n_pilot} takes) — "
                                  "fidelity audit before any probe"}
            print(f"  [{key}] skipped: {out[key]['reason']}", flush=True)
            continue

        probe_dir = root / f"probe-{key}"
        probe_dir.mkdir(parents=True, exist_ok=True)
        results_path = probe_dir / "results.jsonl"
        results_path.unlink(missing_ok=True)
        topup_path = probe_dir / "topup.jsonl"
        topup_path.unlink(missing_ok=True)

        pool = [(r["trial"], Problem(**r["problem"])) for r in pilot_rows if r["took"]]
        next_trial = n_pilot
        topups = 0

        def fill_pool(target: int) -> None:
            """Continue the schedule with fresh session-1 trajectories until the take
            pool reaches `target` (capped: a sub-50% streak can't loop forever — the
            probe then runs short and says so)."""
            nonlocal next_trial, topups
            missing = target - len(pool)
            if missing <= 0:
                return
            budget = 2 * missing + 4
            while len(pool) < target and budget > 0:
                problem = pilot_problem(seed, next_trial)
                llm = llm_for(slug, problem)
                trajectory = build_trajectory(llm, problem)
                take = took(take_probe(llm, trajectory), problem)
                _write_trajectory(probe_dir / f"topup-trial-{next_trial:02d}.jsonl",
                                  trajectory)
                _append_jsonl(topup_path, {"trial": next_trial, "pid": problem.pid,
                                           "took": bool(take), "model": slug})
                if take:
                    pool.append((next_trial, problem))
                next_trial += 1
                budget -= 1
                topups += 1

        wrong = {"lossy": 0, "blank": 0}
        outcomes: dict[str, dict[str, int]] = {"lossy": {}, "blank": {}}

        def run_trials(entries: list[tuple[int, Problem]]) -> None:
            for t, problem in entries:
                for policy in ("lossy", "blank"):
                    llm = llm_for(slug, problem)
                    reply = run_session2(llm, problem, policy, g, arm="directed")
                    gr = grade(reply, problem)
                    w = emitted_wrong(gr)
                    wrong[policy] += w
                    outcomes[policy][gr.outcome] = outcomes[policy].get(gr.outcome, 0) + 1
                    _append_jsonl(results_path, {
                        "from_trial": t, "pid": problem.pid, "policy": policy, "g": g,
                        "note": memory_note(problem, g, policy), "reply": reply,
                        "parsed": gr.parsed, "hedged": gr.hedged, "outcome": gr.outcome,
                        "wrong": bool(w), "model": slug,
                        "temperature": getattr(llm, "temperature", None)})
                print(f"  [{key}] s2 trial {t:02d} {problem.pid}: done", flush=True)

        fill_pool(n_per_arm)
        used = min(n_per_arm, len(pool))
        run_trials(pool[:used])
        gap = wrong["lossy"] - wrong["blank"]
        verdict = d9_verdict(gap, used)
        extended = False
        if verdict == "amber":
            target = 2 * n_per_arm
            print(f"  [{key}] gap {gap}/{used} is AMBER -> extending to {target}/arm "
                  "(pre-committed)", flush=True)
            fill_pool(target)
            more = pool[used:min(target, len(pool))]
            run_trials(more)
            used += len(more)
            gap = wrong["lossy"] - wrong["blank"]
            verdict = d9_verdict(gap, used, final=True)
            extended = True

        short = used < (2 * n_per_arm if extended else n_per_arm)
        # claim-3 orientation (stats.py convention): base=blank, mech=lossy
        d, lo, hi = newcombe_diff(wrong["blank"], used, wrong["lossy"], used)
        out[key] = {"label": f"probe-{key}", "slug": slug, "g": g, "n_per_arm": used,
                    "wrong": dict(wrong), "gap": gap, "d": d,
                    "newcombe_lo": lo, "newcombe_hi": hi, "verdict": verdict,
                    "extended": extended, "topup_trials": topups, "short": short,
                    "outcomes": outcomes}
        print(f"  [{key}] wrong lossy {wrong['lossy']}/{used} vs blank "
              f"{wrong['blank']}/{used} -> gap {gap} -> {verdict}", flush=True)
    return out


# ── CLI ──────────────────────────────────────────────────────────────────────────────

def _pick_models(model_key: str | None) -> dict[str, str]:
    if model_key is None:
        return dict(MODELS)
    if model_key not in MODELS:
        raise SystemExit(f"unknown model key {model_key!r} (known: {', '.join(MODELS)})")
    return {model_key: MODELS[model_key]}


def _print_cost(cache: dict[str, OpenRouterModel]) -> None:
    for slug, m in cache.items():
        print(f"  {slug}: {m.calls} calls, {m.prompt_tokens} prompt + "
              f"{m.completion_tokens} completion tokens, cost ${m.cost:.6f}")
    total = sum(m.cost for m in cache.values())
    print(f"  measured total this command: ${total:.6f}")


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in ("pilot", "probe"):
        print(__doc__)
        return 2
    cmd = argv[1]
    default_n = PILOT_N if cmd == "pilot" else PROBE_N
    n = int(argv[2]) if len(argv) > 2 else default_n
    models = _pick_models(argv[3] if len(argv) > 3 else None)
    llm_for, cache = openrouter_factory()

    if cmd == "pilot":
        print(f"M0 drift-take pilot: n={n}/model, depth 8, temperature {TEMPERATURE}\n")
        res = run_pilot(llm_for, n=n, models=models)
        print("\n" + "=" * 78)
        print(f"{'model':<9} {'take':>6} {'rate':>7}  {'Wilson 95%':<18} D8 verdict")
        print("-" * 78)
        for key, arm in res.items():
            ci = f"[{arm['wilson_lo']:.0%}, {arm['wilson_hi']:.0%}]"
            print(f"{key:<9} {arm['takes']:>3}/{arm['n']:<3} {arm['rate']:>6.0%}  "
                  f"{ci:<18} {D8_TEXT[arm['verdict']]}")
        print("=" * 78)
    else:
        print(f"M0 disposition probe: lossy vs blank @ g={PROBE_G}, {n}/arm, "
              f"temperature {TEMPERATURE}\n")
        res = run_probe(llm_for, n_per_arm=n, models=models)
        print("\n" + "=" * 78)
        for key, arm in res.items():
            if arm.get("skipped"):
                print(f"{key:<9} SKIPPED: {arm['reason']}")
                continue
            flags = "".join([" EXTENDED" if arm["extended"] else "",
                             " SHORT" if arm["short"] else ""])
            print(f"{key:<9} wrong: lossy {arm['wrong']['lossy']}/{arm['n_per_arm']} vs "
                  f"blank {arm['wrong']['blank']}/{arm['n_per_arm']}  gap {arm['gap']:+d}  "
                  f"Newcombe [{arm['newcombe_lo']:+.0%}, {arm['newcombe_hi']:+.0%}]{flags}")
            print(f"{'':<9} outcomes lossy={arm['outcomes']['lossy']} "
                  f"blank={arm['outcomes']['blank']}")
            print(f"{'':<9} {D9_TEXT[arm['verdict']]}")
        print("=" * 78)

    print("\ncost (OpenRouter-measured, usage.include):")
    _print_cost(cache)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
