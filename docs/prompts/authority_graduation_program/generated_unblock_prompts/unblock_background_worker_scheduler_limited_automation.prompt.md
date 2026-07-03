# Unblock Background Worker / Scheduler Limited Automation

Goal:
Prepare or explicitly no-go one limited automation lane for a single already
proven foreground action without enabling broad background autonomy.

Branch:
`codex/unblock-background-worker-scheduler-limited-automation`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- do not add open-ended autonomy
- do not add self-selected background tasks
- do not add provider/model calls
- do not add connector writes/sends
- do not add shell/subprocess execution
- do not add browser/live web execution
- do not add queue consumers, worker pools, daemons, or scheduler runtime until
  exact contracts and controls are proven
- no memory writes or context injection from worker state
- no raw prompt, response, provider payload, connector payload, local path,
  env dump, credential, token, cookie, username, hostname, or secret-like
  persistence
- no public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/background_worker_scheduler_limited_automation_2026_07_03.md`
   - `docs/architecture/BACKGROUND_COWORKER_WORKER_CONTRACT.md`
   - `docs/control_center/operational_maturity_manifest.json`
   - `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
2. Verify that one exact foreground action is already proven at the required
   level and does not depend on blocked provider, connector, shell, browser,
   memory-write, context-injection, or production authority.
3. If no action qualifies, update the blocker and keep this lane blocked.
4. If an action qualifies, implement only scheduler prerequisite contracts:
   - schedule window/cadence refs
   - operator setup receipt refs
   - approval renewal/expiry refs
   - pause/cancel/revoke refs
   - safe-disable refs
   - per-run expected receipt refs
   - run observability refs
   - denial reason refs
   - CLI inspection refs
5. Do not start a worker, scheduler, queue consumer, daemon, provider call,
   connector write, shell command, browser runtime, or background loop.
6. Add or update tests proving:
   - stale/expired/revoked approval blocks;
   - disabled worker/scheduler blocks;
   - unsupported action kinds block;
   - no runtime worker starts;
   - no raw context/payload/path/credential values persist;
   - read-only CLI inspection does not dispatch work.

Tests/verifiers:
- focused background worker/scheduler pytest
- focused run observability pytest
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if routes change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and no worker/scheduler runtime was added
