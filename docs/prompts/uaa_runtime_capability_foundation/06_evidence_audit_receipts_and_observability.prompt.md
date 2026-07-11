# Phase 06: Portable Evidence And Observability

Goal: unify content-free receipts, tamper-aware hash chains, offline
verification, exportable manifests, and operator-readable timelines.

## Required Work

1. Inspect evidence timeline, event ledgers, dispatch/approval/budget/mission
   receipts, redaction, export, CLI/API/UI, and offline verifiers.
2. Define or consolidate a canonical receipt envelope binding safe refs for:
   plan and fingerprint, mission/run/step, current AuthorityLease scope, exact
   approval validation, policy decision, budget reservation/settlement,
   capability/adapter/provider/target, request fingerprint, terminal outcome,
   predecessor hash, redaction status, and verifier version.
3. Implement deterministic canonical serialization and hash chaining with
   content-free portable manifests.
4. Detect tamper, truncation, reorder, replay, duplicate sequence, and
   cross-plan/run/target substitution offline.
5. Add readable CLI/API/macOS timeline and verification posture without raw
   JSON as the primary operator flow.
6. Keep execution evidence structurally distinct from invocation authority.

## Signing Boundary

Implement Ed25519 signing only if a real macOS Keychain-backed lifecycle,
rotation, verification, loss, recovery, and revocation model is proven. If it
is not, retain honest local SHA-256/hash-chain integrity and label signing
blocked. Do not call hashes signatures.

## Required Proofs

- deterministic unchanged verification;
- tamper, truncation, reorder, replay, and substitution rejection;
- missing predecessor and missing required binding rejection;
- cross-run and cross-target receipt denial;
- bounded export and operator-readable verification;
- evidence refs cannot grant authority; and
- no raw prompts, results, pages, logs, paths, provider payloads, credentials,
  environment values, usernames, or hostnames persist.

## Exit

Completion and action evidence are portable, content-free, tamper-aware,
offline-verifiable, redacted, and honestly labeled.
