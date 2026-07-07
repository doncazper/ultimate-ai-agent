# UAA Hermes Runtime Result Classification Posture

Status: Phase 39 repo-safe read model.
Route: `GET /api/runtime/result-classification`
CLI: `scripts/dev/uaa_runtime.py inspect-result-classification`
AuthorityState: `lane-ref:runtime-result-classification-taxonomy` evaluates as
Read-only `workspace/read` through `GET /api/runtime/authority-state` and
`scripts/dev/uaa_runtime.py inspect-authority-state`.

## Full-Strength

Every runtime, tool, command, and agent result is classified before it can
affect product state. Result classes include evidence, mutation, warning,
blocked, proposal, diagnostic, and untrusted data. A mature lane binds each
result envelope to provenance, redaction, verification status, proof, and any
required receipt.

## Repo-Safe

The current implementation is a backend-owned taxonomy only:

- `RuntimeResultClassificationReadModel`
- result classification records for evidence, mutation, warning, blocked,
  proposal, diagnostic, and untrusted data
- provenance policy, redaction policy, receipt requirement, proof binding,
  proof, verifier, blocked authority, and promotion refs
- Control Center labels for the taxonomy
- CLI/API/Core parity
- AuthorityState decision refs for the taxonomy inspection lane

Classification labels are metadata. They do not make runtime output true and do
not grant action authority.

## Blocked / Needs Authority

The following remain blocked:

- treating tool output as truth
- treating tool output as action authority
- mutation without exact receipt
- promotion of unverified output as evidence
- raw output persistence
- provider payload persistence
- Control Center authority minting

## Exact Authority Path

The current allowed AuthorityState decision applies only to reading result
classification labels, verification statuses, provenance policies, redaction
policies, receipt requirements, proof bindings, and blocked-authority refs. It
does not make tool output truth, grant action authority, promote unverified
evidence, permit mutation without receipts, persist output/provider material, or
mint authority from the Control Center.

Future execution-facing result authority requires:

1. result envelope contract
2. provenance record
3. redaction policy and verifier
4. verification status grammar
5. proof binding
6. receipt requirement for mutation results
7. UI labels and product-language tests
8. CLI/API/Core parity
9. regression checks that untrusted data cannot become instructions, truth, or
   authority

Planning text does not grant runtime result authority.
