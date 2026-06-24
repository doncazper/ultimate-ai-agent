# FCC-DOGFOOD-001 Fourteen-Day Private Dogfood Harness

Role: You are a Principal Software Engineer implementing a private evaluation
and evidence-capture lane.

Task: Create a 14-day private dogfood harness for daily-use metrics, friction
notes, useful/irrelevant briefing signals, Action Inbox decisions, and memory
decisions as safe refs.

Requirements:
- The harness must be local/private, safe-ref-only, and explicitly not public
  beta.
- Capture accepted/revised private findings before any beta-readiness or
  execution claim changes.
- Store only redacted summaries, refs, metrics buckets, and manual review
  statuses.
- Make skipped, blocked, missing-source, and not-run states explicit.

Non-goals:
- No telemetry upload, background monitoring, account capture, raw prompts,
  raw logs, raw paths, screenshots with private data, provider/model calls,
  connector writes, public beta, public distribution, or production authority.

Focused checks:
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_product_truth.py --root .`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_087_2b_private_trial_acceptance_ledger.py tests/test_uaa_p1_087_2c_private_trial_manual_review_scaffold.py -q`
- `make frontend-check` if frontend changed
- `git diff --check`
