# Plugin/Skill Ecosystem Boundary

Status: active UAA-P1-024 plugin/skill ecosystem boundary

Scope: production-readiness trust model for plugin, skill, connector-manifest,
and tooling-bundle metadata before any runtime import exists. This boundary is
inspection-only and validation-only. It does not install packages, import
runtime code, execute plugins or skills, call tools, create callable catalogs,
grant connector writes, grant network/browser/mobile/shell authority, or claim
public distribution readiness.

Canonical schema:

```text
docs/schemas/plugin_skill_trust_manifest.schema.json
```

Inspectable catalog implementation:

```text
docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
docs/schemas/inspectable_extension_catalog.schema.json
docs/tooling/EXTENSION_ACTIVATION_GRANTS.md
docs/schemas/extension_activation_grant.schema.json
docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md
```

Related prior governance:

```text
docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md
docs/tooling/PLUGIN_INSTALL_REVIEW.md
docs/tooling/PLUGIN_PERMISSION_MODEL.md
docs/tooling/PLUGIN_PROVENANCE_REVIEW.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
```

## Trust Manifest Fields

Every inspectable extension package must have a trust manifest before it can be
shown as review-ready. The manifest fields are safe refs and redacted summaries
only:

| Field | Required content | Boundary |
|---|---|---|
| Package identity | `package_ref`, package name, package kind, `version_ref`, and `publisher_ref`. | Identity refs are not authority to install, import, or execute. |
| Provenance | `source_ref`, `review_ref`, `license_ref`, and provenance status. | Unknown or blocked provenance keeps the package inactive. |
| Per-file hashes | `file_ref`, `hash_algorithm: sha256`, and `hash_value`. | Hashes validate reviewed package material by ref only; raw package content is not evidence. |
| Declared capabilities | `capability_ref`, capability kind, risk class, and safe purpose. | Capabilities are inspectable before activation and are not callable. |
| Risk class | Highest reviewed package risk: low, medium, high, or critical. | High and critical risk require future scoped approval before activation. |
| Requested grants | `grant-request:*` refs, exact `scope:*` refs, and requested/blocked/future-scoped status. | Requested grants do not grant authority. |
| Activation model | `activation-grant:*`, exact `approval:*`, exact-scope flag, and `runtime_import_allowed: false`. | Activation records are inactive, blocked, revoked, or future-scoped until a later milestone approves execution. |
| Revocation behavior | `revocation:*`, revocation supported, and revocation effect. | Revocation is inspectable and must make grants/catalog entries inactive. |
| Audit refs | `audit:*` refs for manifest review, grant review, and revocation review. | Audit refs are summaries only, not raw logs. |
| Catalog binding | `inspectable-catalog:*`, `callable-catalog:*`, and `callable_catalog_enabled: false`. | Inspectable catalog remains separate from callable catalog. |
| Operator posture | visibility status, trust posture, callable posture, required grant refs, blocked reason, review evidence refs, and safe adoption posture. | UAA runtime capability foundation Phase 09 makes metadata easier to inspect without enabling runtime import or execution. |

The schema also requires `runtime_import_enabled: false` and
`execution_enabled: false`.

## Inspectable Catalog

The inspectable catalog is the only catalog in scope for UAA-P1-024. It can
show safe metadata:

- package identity refs
- provenance status
- per-file hash refs
- declared capability refs
- risk class
- requested grant refs
- activation status
- revocation refs
- audit refs
- blocker refs

Inspectable catalog records are read-only review records. They must not expose
raw package contents, raw manifest contents, raw local paths, raw logs, raw
prompts, raw responses, raw provider payloads, usernames, hostnames, serials,
environment dumps, credential material, cookies, tokens, or private content.

## Callable Catalog Separation

The callable catalog is explicitly out of scope. A package in the inspectable
catalog must not become callable because it has a valid manifest, safe hashes,
declared capabilities, requested grants, activation refs, or approval refs.

Callable catalog entries require a later scoped milestone that separately
defines runtime import authority, execution authority, policy evaluation,
approval binding, revocation enforcement, audit receipts, rollback, tests,
OpenAPI impact, Foundation Gate impact, and release evidence.

Until that later milestone is accepted:

- `callable_catalog_enabled` remains `false`
- `runtime_import_enabled` remains `false`
- `execution_enabled` remains `false`
- activation grants remain inactive, blocked, revoked, or future-scoped
- model/provider output cannot activate a package
- approval refs alone cannot activate a package

## Activation Grants

Activation grants are exact-scope review records, not executable permission.
They must bind:

- `activation-grant:*`
- package ref
- manifest ref
- version ref
- actor ref
- declared capability refs
- requested grant refs
- approval ref
- risk class
- audit refs
- revocation ref
- expiration or staleness rule

Activation is denied when scope is missing, overbroad, stale, revoked,
provenance-blocked, approval-mismatched, or not explicitly covered by a later
runtime milestone. Duplicate activation attempts must be idempotent or blocked
by the activation grant ref.

## Revocation Model

Revocation must be available before activation can be considered in any later
milestone. Revocation records must:

- bind to exact package, manifest, version, actor, activation grant, and scope
  refs
- make inspectable activation status `revoked`, `blocked`, or inactive
- prevent revoked grants from being treated as active
- preserve audit refs and receipt refs
- avoid raw logs, raw paths, raw package content, raw manifest content, raw
  prompts, raw responses, raw provider payloads, usernames, hostnames,
  environment dumps, credential material, or private content

Revocation does not execute package code, unload runtime imports, kill
processes, mutate connectors, or perform shell/subprocess actions in this
milestone because none of those authorities exist here.

## Review States

| State | Meaning | Operator action |
|---|---|---|
| inspectable | Manifest and schema fields are present for review. | Show safe metadata only. |
| blocked | Provenance, hashes, risk, grants, approval, revocation, or audit refs are incomplete or unsafe. | Keep inactive and record blocker refs. |
| future_scoped | Capability may be considered only by a later accepted milestone. | Do not imply shipped support. |
| revoked | Prior activation record is no longer usable. | Keep inactive and preserve audit refs. |

No completed-state language is allowed for blocked, skipped, revoked,
future-scoped, or pending extension work.

## Non-Goals

UAA-P1-024 does not add:

- plugin install
- plugin enablement
- arbitrary plugin execution
- plugin runtime import
- skill runtime import
- callable catalog
- connector writes
- shell execution, command execution, subprocess execution, or process spawn
- unrestricted network access or browser automation
- mobile control or mobile sensor runtime
- autonomous background execution
- model/provider output as authority
- raw package content, raw manifest content, raw prompt, raw response, raw
  provider payload, raw path, raw log, username, hostname, serial, environment
  dump, credential material, cookies, tokens, or private content in evidence
- public release, public distribution, hosted production support, signed
  installer readiness, or production authority

## Known Gaps

- Static package review remains future-scoped to UAA-P2-048.
- UAA-P2-049 adds read-only inspectable catalog route/model/schema coverage in
  `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`; callable catalog and runtime
  import remain not scoped.
- UAA-P2-050 adds exact-scope activation and revocation records in
  `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`; runtime activation, runtime
  import, callable catalog, and execution remain not scoped.
- UAA-P2-051 records MCP/A2A compatibility as strategy/watchlist only in
  `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`; runtime authority,
  connector writes, plugin execution, broad tool invocation, and network
  authority remain not scoped.
- UAA runtime capability foundation Phase 09 adds final operator posture fields and
  `scripts/dev/uaa_extensions.py inspect-catalog`; plugin runtime import
  remains blocked, connector writes remain blocked, and production authority
  remains blocked.
- Runtime import and callable execution remain disabled until a later accepted
  milestone explicitly grants and tests them.

## Rollback

To roll back UAA-P1-024, remove this document, the trust-manifest schema,
documentation-integrity checks, docs index and canonical-map links,
product-truth/Kanban/roadmap updates, and any release evidence references added
for this task. Until a replacement boundary is accepted, plugin and skill
ecosystem work should remain blocked or future-scoped.
