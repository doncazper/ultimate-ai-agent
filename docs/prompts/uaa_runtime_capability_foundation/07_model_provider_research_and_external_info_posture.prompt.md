# Phase 07: Extensibility Ecosystem

Goal: mature existing capability and extension catalogs without equating
visibility, installation, or readiness with request authority.

Inspectable never means callable.

## Required Work

1. Inspect capability availability, extension catalog, skill/plugin/MCP
   boundaries, activation grants, compatibility, CLI/API/UI, manifests, and
   developer validation tools.
2. Normalize backend-owned declaration, compatibility, configuration, health,
   authority-evaluation eligibility, budget, safe-disable, provenance, version,
   hash/signature-when-real, activation, and rollback receipt posture.
3. Preserve unknown, stale, incompatible, unhealthy, unconfigured, blocked,
   and budget-unknown states. Safe-disable overrides all positive readiness.
4. Add deterministic developer validation for manifest shape, provenance,
   version compatibility, hashes, blocked reasons, redaction, and rollback.
5. Expose readable inspectable catalogs through CLI/API/macOS UI. Catalog and
   manifest presence never imply a globally callable or authorized state.
6. Runtime import or callable extensions remain denied unless one isolated
   exact adapter proves current policy, exact approval, current lease, target,
   mission/run, deadline, budget, kill switch, readiness, idempotency,
   redaction, rollback, safe-disable, and receipts at final start.

## Required Proofs

- inspectable entries remain non-callable without an exact request decision;
- unknown/stale compatibility and health fail closed;
- version/hash/provenance mismatch blocks;
- safe-disable and missing budget override readiness;
- activation metadata alone grants no authority;
- rollback and revocation receipts are safe and idempotent; and
- arbitrary plugin, skill, MCP, package, provider, or inherited capability
  execution remains denied.

## Non-Goals

No arbitrary runtime import, remote MCP, marketplace install, package
execution, connector write, provider inheritance, capability-class promotion,
public distribution, production authority, or broad extension enable switch.

## Exit

The ecosystem is inspectable, versioned, validated, and rollback-aware while
all callability remains exact and request-scoped or truthfully blocked.
