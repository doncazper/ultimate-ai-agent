# UAA Hermes Runtime Logging Profile Posture

Status: Phase 38 repo-safe read model.  
Route: `GET /api/runtime/logging-profile`  
CLI: `scripts/dev/uaa_runtime.py inspect-logging-profile`

## Full-Strength

UAA can switch between normal quiet operation and redacted troubleshooting
detail for runtime, policy, evidence, and UI flows. A mature lane would let the
operator enable a scoped verbose profile for a bounded TTL, prove redaction,
bind the proof to an operator decision, and safely disable the profile without
turning raw logs into durable product truth.

## Repo-Safe

The current implementation is backend-owned inspection only:

- `RuntimeLoggingProfileReadModel`
- quiet normal, redacted troubleshooting, and forensic safe-ref profile records
- flag scope, TTL policy, retention policy, redaction policy, redaction verifier,
  proof, blocked authority, and promotion refs
- CLI/API/Core parity
- Control Center display of the current quiet-default posture

No logging flag is toggled. No raw logs are persisted.

## Blocked / Needs Authority

The following remain blocked:

- raw log persistence
- raw prompt persistence
- raw response persistence
- provider payload persistence
- raw local path persistence
- credential or secret-like material persistence
- remote telemetry export
- background log streaming
- Control Center authority minting

## Exact Promotion Path

Promotion to a real verbose/details toggle requires:

1. exact flag scope
2. operator approval binding
3. bounded TTL and automatic expiry
4. redaction verifier fixtures
5. retention policy and cleanup posture
6. local-only proof record
7. safe-disable behavior
8. no raw prompt, response, provider payload, path, log, or credential storage
9. CLI/API/Core parity
10. focused tests and product-language checks

Planning text does not grant logging authority. The default profile remains
quiet and non-verbose.
