# Credential Vault Backend V1

Status: active local safe-ref backend.

Credential Vault Backend V1 adds a local safe-ref ledger behind the provider
credential vault posture contracts. It can record enroll, revoke, and
rotation-required posture for a `secret_ref`, and it can be inspected through
`scripts/inspect_credential_vault_backend.py`.

This lane does not persist recoverable secret material. The enrollment value is
transient input to the Python core, and durable records contain only safe refs,
operation posture, blocker codes, and redacted receipts. The backend does not
authorize provider validation, does not authorize provider invocation, does not
call provider SDKs, does not call the network, does not invoke models, and does
not grant billing authority.

Enroll, revoke, and rotation-required mutations require exact
`LocalApprovalAuthority` scope. The approval ref is recorded as posture evidence
only; approval presence still does not authorize provider validation, secret
resolution, provider SDK calls, model invocation, provider invocation, or billing
authority.

In shorter form: backend V1 does not authorize provider validation and does not
authorize provider invocation.

Implemented contracts:

- `LocalCredentialVaultEnrollmentRequest` accepts transient enrollment input,
  exact safe refs, and an exact approval ref, then records only a `secret_ref`
  and receipt refs.
- `LocalCredentialVaultRecord` stores safe refs for provider, model, credential,
  policy, approval scope, budget decision, expected receipt, revocation, and
  rotation posture.
- `LocalCredentialVaultOperationReceipt` records enroll, revoke, and
  rotation-required outcomes as redacted safe refs only.
- `LocalCredentialVaultInspectionSnapshot` exposes current posture without
  creating state or revealing secret material.

Supported posture:

- `vault_not_configured`
- `secret_ref_available`
- `secret_ref_revoked`
- `rotation_required`
- `vault_blocked`

Blocked by this lane:

- No secret resolution API.
- No raw secret display.
- No mutation without exact LocalApprovalAuthority approval.
- No provider credential validation.
- No provider SDK calls.
- No model invocation.
- No provider invocation authority.
- No billing authority.
- No invocation authority from vault presence.

Product language rules:

- `secret_ref_available` means the local ledger has a durable safe reference for
  future exact-scope review. It is not a usable secret handle.
- `secret_ref_revoked` blocks future use until a later scoped lane defines any
  revocation-aware validation or invocation behavior.
- `rotation_required` is operator posture only.
- Backend V1 is not a provider connection, not credential validation, not a
  provider runtime, and not a billing or spend grant.
