# Credential Vault Contract Shell

Status: active contract shell.

The Credential Vault Contract Shell defines metadata-only provider credential
vault records before any live provider use. It is inspectable through
`scripts/inspect_credential_vault_contract.py` and verified by
`scripts/verify_credential_vault_contract_shell.py`.

Backend distinction: `docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md`
documents the separate local safe-ref ledger for enroll/revoke/rotation posture.
The shell surface remains metadata-only, and backend V1 still does not expose
secret resolution, provider validation, provider SDK calls, model invocation, or
provider invocation authority.

This shell does not collect, store, resolve, validate, rotate, or reveal secret
material. Vault records are safe refs only and do not authorize provider
validation, provider invocation, provider SDK calls, model invocation, billing
authority, or runtime provider use.

Implemented contracts:

- `ProviderCredentialVaultPosture` defines `vault_not_configured`,
  `vault_blocked`, `secret_ref_available`, `secret_ref_revoked`,
  `rotation_required`, `validation_required_but_blocked`, and
  `invocation_requires_approval`.
- `ProviderCredentialVaultRecord` carries exact future scope refs:
  `provider_ref`, `model_ref`, `credential_ref`, `policy_ref`,
  `approval_scope_ref`, `budget_decision_ref`, `expected_receipt_ref`, and
  `revocation_ref`.
- `ProviderCredentialVaultSnapshot` exposes the current metadata-only vault
  shell for CLI inspection and tests.

Blocked by this lane:

- No secret collection UI.
- No key paste field.
- No OS keychain or credential manager access.
- No storage of secret material through the contract shell.
- No provider validation call.
- No provider SDK.
- No model invocation.
- No validation authority from vault presence.
- No invocation authority from vault presence.

Product language rules:

- `secret_ref_available` means a safe reference may exist for future exact
  scope review. It is not a usable secret handle.
- `secret_ref_revoked` means future use must remain blocked until a later
  scoped milestone defines revocation handling and receipts.
- `rotation_required` is a review posture only.
- `validation_required_but_blocked` does not authorize provider validation.
- `invocation_requires_approval` does not authorize provider invocation.

Promotion rule:

The Exact-Approved Provider Invocation Promotion Plan in
`docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md`
defines the next planning-only gate. A later runtime lane must still introduce
exact approval, CostGovernor decision binding, policy validation, redacted
receipts, revocation posture, and safe-disable or rollback posture before any
provider credential validation or provider invocation can occur.
