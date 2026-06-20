# Repo Awareness Benchmark Log

Status: active deterministic benchmark ledger
Schema: `uaa_repo_awareness_benchmark.v1`

This ledger lets reviewers ask how the repository changed over time without
depending on chat memory. It stores repo-tracked snapshots with deterministic
scores, tiers, blockers, metrics, and evidence refs.

It does not add backend routes, Control Center UI, model calls, network fetches,
background workers, new dependencies, production authority, public release
claims, broad autonomy, shell authority, browser authority, connector writes,
plugin runtime import, mobile control, raw prompt export, raw response export,
raw provider payload export, raw path export, raw log export, or credential
material.

## Commands

Create a manual review snapshot:

```bash
.venv/bin/python scripts/benchmark_repo_awareness.py snapshot --reason manual_review --write
```

Create the weekly review snapshot when Codex or a human reviewer is prompted:

```bash
.venv/bin/python scripts/benchmark_repo_awareness.py snapshot --reason weekly_review --write
```

Compare the latest snapshot with the newest snapshot at or before a window:

```bash
.venv/bin/python scripts/benchmark_repo_awareness.py compare --since 24h
.venv/bin/python scripts/benchmark_repo_awareness.py compare --since 7d
```

Compare exact snapshots:

```bash
.venv/bin/python scripts/benchmark_repo_awareness.py compare --from snapshots/example.json --to latest.json
```

## Scoring

Scores are 0-100 with these tiers:

| Tier | Score range |
|---|---:|
| `blocked` | 0-39 |
| `emerging` | 40-59 |
| `stabilizing` | 60-74 |
| `rc_watch` | 75-89 |
| `rc_ready` | 90-100 |

Category weights:

| Category | Weight |
|---|---:|
| Module maturity | 20 |
| Route and product surface | 20 |
| Verifier and evidence coverage | 20 |
| Safety boundary health | 20 |
| Performance state | 10 |
| RC readiness blockers | 10 |

Numeric scores are deterministic and evidence-based only. Narrative summaries
may explain a score, but they do not change the score.

## Weekly Model

Weekly review is reminder plus manual command. There is no unattended repo
write and no automatic commit. This keeps benchmark history intentional and
reviewable.

## Verification

Run:

```bash
.venv/bin/python scripts/verify_repo_awareness_benchmark.py
.venv/bin/python -m pytest tests/test_repo_awareness_benchmark.py
```

The verifier checks schema currentness, latest snapshot validity, snapshot
ledger presence, score/tier consistency, safety flags, safe evidence refs, and
raw/private fragment denial.

## Rollback

Rollback is to remove the benchmark files added for this lane and remove the
`verify_all.py` hook. For a single bad benchmark run, delete that snapshot and
regenerate `latest.json`, `latest.md`, and `index.md` from the intended latest
snapshot.
