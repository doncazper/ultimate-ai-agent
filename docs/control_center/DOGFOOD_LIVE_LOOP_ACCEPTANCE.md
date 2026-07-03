# Dogfood Live Loop Acceptance

Status: implemented local dogfood acceptance proof.

Dogfood Live Loop Acceptance proves one deterministic repo-local dogfood loop
through backend-owned state:

Start Here -> Today -> Action Inbox -> exact local task commit -> receipt ->
Evidence -> Proof Detail -> Memory binding -> Trust posture.

This is a local deterministic fixture and verifier lane. It uses safe refs and
redacted summaries only, requires no external account, provider, connector,
browser, web, shell, scheduler, or credential runtime, and persists no raw
private payloads.

No broad authority is added. The only mutation exercised by the fixture is the
already graduated exact `local_task_create` local task commit lane, using the
existing backend approval, idempotency, receipt, evidence, rollback, and
safe-disable posture.

## Repo-Local Inspection

- CLI: `.venv/bin/python scripts/dev/uaa_founder_loop.py inspect-dogfood-live-loop --seed-fixture`
- Verifier: `.venv/bin/python scripts/verify_dogfood_live_loop_acceptance.py`
- Focused backend tests: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dogfood_live_loop_acceptance.py -q`
- Focused frontend test: `cd apps/control-center && npm test -- --run src/App.test.tsx -t "dogfood loop"`

## Acceptance Evidence

The verifier builds a temporary `FounderLoopRepository`, seeds or replays one
deterministic local approval and local task commit through the exact Python Core
contracts, then proves these shared refs across the backend read models:

- Start Here reports one governed local loop and the next safe action.
- Today exposes the same run, action, proof, evidence, and memory refs.
- Action Inbox shows the local task lane as receipt-recorded after commit.
- Proof Detail includes the local task commit proof and receipt refs.
- Evidence and Memory link back to the same run/action/proof/evidence refs
  through the combined Evidence/Memory binding.
- Trust labels local task commit as exact approval required and keeps external
  mutation plus standing authority blocked.

## Still Blocked

This lane does not grant provider/model calls, connector writes or sends,
browser automation, live web/runtime fetching, shell/subprocess execution,
background autonomy, hidden context injection, broad approvals, memory truth
authority, public distribution, or production authority.
