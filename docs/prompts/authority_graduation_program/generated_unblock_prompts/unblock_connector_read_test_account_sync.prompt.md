# Unblock Connector Read Test-Account Sync

Goal:
Perform or explicitly no-go one exact test-account, read-only connector metadata
sync without granting broad connector read authority.

Branch:
`codex/unblock-connector-read-test-account-sync`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- do not broaden connector read authority beyond one named test connector
- no production accounts
- no connector writes, sends, archive/delete/label/move, CRM writes, or
  calendar writes
- no background polling, scheduler, or autonomous sync
- no provider/model calls
- no browser automation or shell execution
- no memory writes or context injection from connector data
- no raw message body, contact, account, token, cookie, attachment, calendar
  description, path, credential, or source payload persistence
- no public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/connector_read_test_account_sync_2026_07_03.md`
   - `docs/connectors/CONNECTOR_READ_ONLY_RUNTIME.md`
   - `docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`
   - `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
   - `scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py`
2. Verify whether a safe test connector account, least-scope OAuth or
   credential grant, exact adapter scope, revocation path, and redacted receipt
   store are available for one named read-only adapter.
3. If any prerequisite is missing, do not connect to a provider account. Update
   the blocker report with the missing prerequisite and keep the lane blocked.
4. If every prerequisite is present, implement exactly one foreground
   test-account metadata sync through a backend-owned connector read model.
5. Persist only safe refs, redacted metadata summaries, approval/account scope
   refs, evidence refs, audit refs, idempotency refs, and cache purge refs.
6. Add CLI inspection over the same backend-owned connector read receipts.
7. Add or update tests proving:
   - production accounts are rejected;
   - least-scope read authorization is required;
   - raw body/contact/account/token/cookie/attachment/calendar/path/credential
     values are not persisted or rendered;
   - repeated sync inspection is idempotent;
   - revocation/cache purge posture is visible;
   - connector writes/sends and background polling remain blocked.

Tests/verifiers:
- focused connector read pytest for the new exact adapter/read model
- `.venv/bin/python scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if routes change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and the scope remains exactly one test-account
  read-only connector metadata sync
