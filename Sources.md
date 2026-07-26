# Sources

| Source | Location | Type | Authoritative for |
|--------|----------|------|-------------------|
| Reclaim Evaluation paper (v2) | https://arxiv.org/abs/2606.25449 | paper | The claim under reproduction: definitions of the wall, policies, g-sweep, and the paper's own numbers |
| Author's released harness | https://github.com/collapseindex/reclaim-eval (local clone used as oracle only, per D1) | code / oracle | The cross-check cell — their protocol as actually implemented, incl. its parser bug and empty `data/results/` |
| KICKOFF brief | `docs/KICKOFF.md` | brief | Approved scope, phased plan, risks, gate record — scope source of truth |
| Milestone briefs M0–M5 | `docs/M0-BRIEF.md` … `docs/M5-BRIEF.md` | signed briefs | Pre-committed designs, CI gates, equivalence margins, and verdict mappings for each stage |
| Decision ledger | `DECISIONS.md` | ledger | Every decision D1–D31 with options + rationale (append-only) |
| Roadmap | `ROADMAP.md` | status doc | Milestone verdict tables, cost ledgers, checkpoint records |
| Learning notes | `LEARNING.md` | teaching notes | Plain-English explanations + vocabulary for defending every decision |
| Run evidence | `evidence/m0/` … `evidence/m5/` | raw exports | The archived trial-level records every gated statistic is computed from |
| Raw run outputs | `runs/` | raw exports | Per-run request/response logs backing the evidence |
| Session logs | `docs/session-logs/` | transcripts | Blow-by-blow session history via `/wrap` |
| Replication paper + presenter brief | `docs/paper/` (branch `docs/paper-presenter-brief`, PR #34 — unmerged) | write-up | The outward-facing account; every statistic traced to the committed record |
