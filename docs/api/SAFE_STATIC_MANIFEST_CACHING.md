# Safe Static Manifest Caching

Status: active UAA-P1-042 safe static manifest caching

Scope: process-local caching for `/api/manifest` static metadata only.

UAA-P1-042 caches safe static API manifest data so repeated manifest reads do
not rebuild route inventory objects unnecessarily. The cache is in-memory only,
process-local, and rebuilt whenever the static route fingerprint changes.

## Cached Fields

The cache may store only:

- `title`
- `api_version`
- `package_version`
- `active_baseline`
- `route_count`
- `route_groups`
- `routes`
- `capabilities_declared`
- `capabilities_blocked`
- `no_runtime_integrations`

These fields are generated from FastAPI route metadata, package version,
baseline label, and static capability declarations.

## Explicit Exclusions

The cache must not store:

- `foundation_gate_status`
- `local_auth_policy`
- policy decisions or policy outcomes
- approvals or approval decisions
- runtime authority
- user data
- secrets
- mutable state
- prompts, responses, provider payloads, logs, hostnames, usernames,
  environment dumps, raw local paths, or credential material

`foundation_gate_status` and `local_auth_policy` are attached after the static
cache lookup so each call can carry the live caller-provided status and current
dev-only bypass posture. PolicyEngine and LocalApprovalAuthority decisions
remain outside the manifest cache.

## Invalidation

The static cache is invalidated by:

- app title change
- package version change
- active baseline change
- route path, method, operation id, tag, or summary change
- declared capability list change
- blocked capability list change
- manual cache clear

Route side-effect classes are rebuilt when the route fingerprint changes, so a
new route cannot silently inherit a stale risk posture.

## Staleness Risk

Known residual risk is limited to in-process code that mutates route behavior
without changing route metadata. That is not a supported production mutation
path. Reviewed route changes must update OpenAPI and API manifest checks, which
exercise cache invalidation.

## Rollback

To roll back UAA-P1-042, revert the static cache helpers in
`src/ultimate_ai_agent/api/manifest.py`, the cache tests in
`tests/test_api_manifest.py`, this document, and the verifier/Kanban/roadmap
links added for UAA-P1-042.
