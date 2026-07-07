# Exact-Approved Provider Credential Validation Lane

Status: AuthorityLease-gated exact-approved validation lane implemented;
runtime provider/model use remains blocked outside this exact non-invoking
validation scope.

This lane adds one isolated provider credential validation path:
`POST /control-center/providers/credentials/validate`. It can validate one
OpenAI-compatible provider credential only after an active AuthorityLease grants
`provider_model_calls/execute`, exact `LocalApprovalAuthority` scope, policy
scope, idempotency, revocation/safe-disable refs, and a redacted validation
receipt ref are present. The default app posture is authority-required because
the API route only reads persisted active leases; without one it returns a
blocked authority decision before exact approval or adapter execution. Even with
authority, the lane remains blocked until exact approval, an enabled adapter,
and an injected validation transport are present.
The public request contract is safe-ref-only: it accepts `credential_ref` and
scope refs, not raw credential material. Transient credential material can only
enter the core through an exact-scoped internal adapter/vault handoff and is
never serialized, logged, displayed, or persisted.

The Python core contract lives in
`src/ultimate_ai_agent/core/providers/credential_validation.py`. Operator CLI
inspection is available through
`scripts/inspect_provider_credential_validation_lane.py`. Verification is
provided by `scripts/verify_provider_credential_validation_lane.py` and
`tests/test_provider_credential_validation_lane.py`.

## Required Scope

- `credential_ref`
- `provider_ref`
- active `provider_model_calls/execute` AuthorityLease
- exact approval scope
- `policy_ref`
- `idempotency_ref`
- `validation_receipt_ref`
- `revocation_ref`
- `safe_disable_ref`
- provider manifest and allowlist refs
- exact provider endpoint allowlist ref
- rate budget ref
- redacted validation summary ref

The OpenAI-compatible adapter shell has no built-in stdlib/provider SDK
transport. A later scoped enablement must inject an approved transport inside
the exact validation adapter boundary; otherwise the lane records
`validation_blocked` with `PROVIDER_VALIDATION_TRANSPORT_NOT_CONFIGURED`. Direct
core and verifier paths may inject an explicit provider validation lease for
tests; this does not create standing provider/model authority.

The only returned statuses are:

- `credential_valid`
- `credential_invalid`
- `validation_blocked`

Receipts store safe refs only, including redacted receipts for blocked or
unknown provider-network attempts after exact approval. Raw credentials,
provider payloads, prompts, responses, usernames, hostnames, local paths, env
dumps, logs, and secrets must not appear in receipts, evidence, docs, tests, UI,
or CLI output.

## Non-Goals

- No model invocation.
- No chat or completions calls.
- No provider SDK.
- No provider payload persistence.
- No raw credential display.
- No public raw-secret entry route.
- No broad provider router.
- No fallback.
- No billing authority.
- No autonomous or background calls.
- No production authority.

Credential validation is not provider runtime authority. A valid credential
receipt only says the exact validation check returned `credential_valid`; it
does not authorize invocation, routing, fallback, spending, or provider output
authority. The required AuthorityLease authorizes only this exact
non-invoking validation decision path and does not authorize provider SDK calls,
chat/completions, billing, payload persistence, fallback, or background use.
