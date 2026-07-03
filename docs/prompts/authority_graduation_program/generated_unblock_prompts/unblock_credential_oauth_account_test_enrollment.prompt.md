# Unblock Credential / OAuth / Account Test Enrollment

Goal:
Perform or explicitly no-go one test-account credential/OAuth enrollment and
revocation cycle without granting production account or broad connector
authority.

Branch:
`codex/unblock-credential-oauth-account-test-enrollment`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- test account only
- no production accounts
- no broad OAuth scopes
- no raw secret, token, cookie, session, client secret, account identifier, or
  credential display/export/persistence
- no secret resolution API unless exact scope is separately approved
- no account sync unless Connector Read lane grants it
- no connector writes/sends
- no provider/model call from credential presence
- no browser automation or shell execution
- no background account polling
- no public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/credential_oauth_account_test_enrollment_2026_07_03.md`
   - `docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`
   - `docs/control_center/PROVIDER_CREDENTIAL_VALIDATION_LANE.md`
   - `docs/production/ACCOUNT_CONNECTOR_CONTRACT_REVIEW.md`
2. Verify whether an approved test account, OAuth client boundary,
   least-scope allowlist, revocation path, and no-token-persistence receipt
   store are available.
3. If any prerequisite is missing, do not perform OAuth/account enrollment.
   Update the blocker report and keep the lane blocked.
4. If every prerequisite is present, implement exactly one test-account
   enrollment and revocation cycle:
   - safe account/provider refs
   - least-scope refs
   - approval refs
   - redacted vault/account posture refs
   - revocation/rotation refs
   - idempotency/audit/evidence/receipt refs
   - CLI inspection refs
5. Do not grant connector read/write authority from enrollment alone.
6. Add or update tests proving:
   - production accounts are rejected;
   - broad scopes are rejected;
   - tokens/secrets/cookies are not persisted or rendered;
   - revocation/rotation posture is visible;
   - connector read/write and provider/model authorities remain blocked.

Tests/verifiers:
- focused credential/OAuth/account pytest
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_credential_vault_backend_v1.py tests/test_provider_credential_validation_lane.py tests/test_m113_secrets_boundary_credential_vault.py tests/test_m114_account_connector_contract_review.py -q`
- `.venv/bin/python scripts/verify_credential_vault_backend_v1.py`
- `.venv/bin/python scripts/verify_provider_credential_validation_lane.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if routes change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and no production-account/broad credential authority
  was added
