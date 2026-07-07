# UAA Hermes Runtime Managed Scope Policy

Status: Hermes Runtime Adoption Phase 27, AuthorityState-bound repo-safe read model.

## Full-Strength

UAA can pin safe runtime policy defaults for a local operator or team without
hiding what is pinned, why it is pinned, which source has precedence, and what
drift needs review.

## Repo-Safe

Phase 27 adds Python Core ownership for a read-only local policy profile:

- `RuntimeManagedScopePolicyReadModel`
- `GET /api/runtime/managed-scope-policy`
- `scripts/dev/uaa_runtime.py inspect-managed-scope-policy`
- Authority mapping `lane-ref:runtime-managed-scope-policy-read-model` as
  Read-only `workspace/read`
- Control Center `/runtime` managed scope card

The read model exposes pinned source refs, source kinds, precedence, checksum
refs, drift warning refs, rollback refs, admin/operator proof refs, blocked
authority refs, promotion path refs, AuthorityState route/CLI/mapping/catalog/
decision/reason refs, unsupported adapter refs, and decision-bound snapshot
hashes. It does not write system config, apply privileged settings, deliver MDM
profiles, manage secrets, accept unsigned runtime config overrides, or claim
production enforcement.

## Blocked / Needs Authority

- Privileged writes.
- MDM delivery.
- Managed secrets.
- Unsigned runtime config overrides.
- Production enforcement claims.
- Control Center minting authority.
- Raw config, local path, account material, credential material, or protected
  material persistence.

## Exact Promotion Path

1. Define a local config source and safe source ref grammar.
2. Define policy source precedence and verification rules.
3. Bind protected material only as redacted refs.
4. Add rollback and safe-disable proof.
5. Add admin/operator proof with CLI/API/Core/Control Center parity.
6. Add focused tests for drift, override denial, redaction, idempotency,
   route classification, and product-language boundaries.

## Verification

- `tests/test_hermes_runtime_managed_scope_policy.py`
- `scripts/verify_hermes_runtime_adoption_phase_27.py`
