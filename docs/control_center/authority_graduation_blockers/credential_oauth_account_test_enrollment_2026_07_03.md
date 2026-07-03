# Credential / OAuth / Account Test Enrollment Blocker

Status: blocked, no OAuth/account runtime promoted
Lane: Credential / OAuth / Account
Attempted promotion: test-account credential/OAuth enrollment and revocation
Date: 2026-07-03

## Existing Verified Posture

UAA already has safe credential/account foundations:

- Credential Vault Backend V1:
  - doc: `docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`
  - script: `scripts/inspect_credential_vault_backend.py`
  - verifier: `scripts/verify_credential_vault_backend_v1.py`
  - test: `tests/test_credential_vault_backend_v1.py`
- Provider credential validation exact lane:
  - doc: `docs/control_center/PROVIDER_CREDENTIAL_VALIDATION_LANE.md`
  - script: `scripts/inspect_provider_credential_validation_lane.py`
  - verifier: `scripts/verify_provider_credential_validation_lane.py`
  - test: `tests/test_provider_credential_validation_lane.py`
- M113/M114 production readiness contracts:
  - `docs/production/SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT.md`
  - `docs/production/ACCOUNT_CONNECTOR_CONTRACT_REVIEW.md`
  - `tests/test_m113_secrets_boundary_credential_vault.py`
  - `tests/test_m114_account_connector_contract_review.py`

The current vault records safe `secret_ref` ledger posture and redacted receipts
only. It does not persist recoverable secret material, resolve secrets for
runtime use, perform OAuth flows, exchange tokens, connect accounts, sync
accounts, or grant provider/model/connector authority.

## Why This Was Not Unblocked

The requested promotion requires one test-account credential/OAuth enrollment
cycle with least-privilege scopes, redacted refs, revocation/rotation proof, no
secret leakage, and connector read/write boundary tests.

That promotion was not safe in this run because:

- no approved test account was supplied;
- no OAuth provider/client boundary is scoped;
- no least-scope allowlist exists for one account connector;
- no token exchange/no-token-persistence contract exists;
- no OAuth revocation/rotation proof exists;
- Connector Read test-account sync remains blocked;
- Connector Write/Send remains blocked;
- current vault posture intentionally does not expose secret resolution or
  account connector runtime.

## Missing Contract / Test / Evidence

- exact test-account enrollment contract;
- OAuth provider/client metadata refs without raw client secrets;
- least-privilege scope allowlist;
- token exchange boundary with no token persistence;
- revocation and rotation proof;
- no secret display/export tests;
- production-account rejection tests;
- connector read boundary integration proving no broad sync;
- connector write/send denial proof;
- CLI inspection over redacted account/OAuth posture only.

## Smallest Next Safe Action

Run a dedicated credential/OAuth unblock PR that either enrolls one approved
test account through a least-scope no-token-persistence OAuth contract, or
records a no-go if test-account, OAuth client, revocation, and redaction
prerequisites are unavailable.

## Authority Still Blocked

- production accounts
- broad scopes
- raw secret display or export
- secret resolution/runtime use
- OAuth flow and token exchange
- cookie/session handling
- account sync
- connector reads beyond separately graduated read-only sync
- connector writes/sends
- provider/model calls from credential presence
- browser automation
- background account polling
- public beta, public release, or production authority
