# Unblock Connector Write / Send Test Target

Goal:
Perform or explicitly no-go the first exact send-to-self/test-target connector
mutation after the connector draft-only proposal lane, without granting broad
connector write authority.

Branch:
`codex/unblock-connector-write-send-test-target`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- do not broaden connector write/send authority beyond one named test connector
- no production accounts or production targets
- no connector read/account/OAuth shortcut if those prerequisite lanes remain
  blocked
- no archive/delete/label/move/calendar write/CRM write
- no background polling, scheduler, retry worker, or autonomous delivery
- no provider/model calls
- no browser automation, web runtime, or shell execution
- no memory writes or context injection from connector data
- no raw body, contact, account, token, cookie, attachment, calendar
  description, local path, credential, prompt, response, provider payload, or
  source payload persistence
- no public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/connector_write_send_test_target_2026_07_03.md`
   - `docs/control_center/authority_graduation_blockers/connector_read_test_account_sync_2026_07_03.md`
   - `docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md`
   - `docs/architecture/CONNECTOR_DELIVERY_SEMANTICS_CONTRACT.md`
   - `docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER.md`
   - `docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK.md`
2. Verify connector read and test-account credential/OAuth prerequisites first.
   If either prerequisite is still blocked, do not implement send/write
   behavior. Update the blocker report and keep this lane blocked.
3. Verify the connector draft-only proposal lane exists and bind the test
   send/write attempt to exactly one existing draft proposal ref.
4. If prerequisites are available, implement exactly one backend-owned
   send-to-self/test-target lane for one named test connector and one
   allowlisted target.
5. Persist only safe refs, redacted subject/body-summary refs, target/session
   refs, approval refs, idempotency refs, evidence refs, receipt refs,
   audit/replay refs, rollback/safe-disable refs, and blocked send/write refs.
6. Do not add broad send controls; any Control Center surface must call the same
   exact backend contract and stay disabled if the contract is unavailable.
7. Add CLI inspection over the same backend-owned test-send/write receipts.
8. Add or update tests proving:
   - production accounts and production targets are rejected;
   - target allowlist is required;
   - exact approval and idempotency are required;
   - raw body/contact/account/token/cookie/attachment/calendar/path/credential
     values are not persisted or rendered;
   - duplicate draft/send attempts replay safely;
   - connector sends/writes, background workers, retries, and broad account sync
     remain blocked unless separately proven.

Tests/verifiers:
- focused connector delivery/write pytest for the new exact lane
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_connector_delivery_semantics_contract.py tests/test_m127_connector_write_dry_run_planner.py tests/test_m128_connector_write_execution_low_risk.py -q`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if routes change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and the scope remains exactly one test connector
  send-to-self/test-target action or an explicit no-go
