# Ultimate AI Agent Master Plan v0.29.4

Status: active release packet
Current through: v0.29.4
Purpose: Master-plan summary for documentation archive reference repair and self-maintaining docs policy.

## Scope

v0.29.4 is docs/index/verifier/version/file-organization only.

## Implemented

- Archives active-looking historical version verifiers under
  `docs/archive/releases/vX_Y_Z/`.
- Removes stale Ruff excludes for retired verifier paths.
- Adds `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`.
- Updates active root, docs index, canonical map, roadmap, route inventory,
  test strategy, release notes, and Foundation Gate implementation plan.
- Strengthens `scripts/verify_documentation_integrity.py` so active validation
  fails if historical version verifiers return to root or active `scripts/`.
- Keeps future release packets under `docs/archive/releases/vX_Y_Z/`.

## Boundaries

v0.29.4 adds no M26 Grounded Recall Router, Context Pack Builder, backend
routes, frontend features, runtime/model/provider calls, memory writes, tool
execution, dependencies, security architecture changes, or production
authority.

M25 remains implemented/hardened. v0.29.2 remains the accepted pre-M26 security
hardening baseline. v0.29.3 remains preserved as historical documentation
organization work superseded by this repair. M26 remains planned/provisional.
