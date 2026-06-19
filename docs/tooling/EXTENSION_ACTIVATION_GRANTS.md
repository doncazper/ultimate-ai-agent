# Extension Activation Grants

Status: active UAA-P2-050 extension activation grants

Scope: exact-scope activation and revocation records for inspectable extension
metadata. This document defines review records only. It does not add plugin
runtime import, arbitrary plugin execution, callable catalog behavior,
connector writes, shell/subprocess execution, unrestricted network or browser
automation, mobile control, autonomous background execution, public
distribution, or production authority.

Canonical schema:

```text
docs/schemas/extension_activation_grant.schema.json
```

Canonical implementation:

```text
src/ultimate_ai_agent/core/extension_catalog/contracts.py
tests/test_extension_activation_grants.py
```

Related catalog:

```text
docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
docs/schemas/inspectable_extension_catalog.schema.json
docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md
```

## Grant Record

An extension activation grant record must include:

| Field | Required binding | Safety rule |
|---|---|---|
| `activation_grant_ref` | Exact grant record ref. | Duplicate grant refs are denied. |
| `package_ref` | Exact package ref. | Package identity is not install or import authority. |
| `manifest_ref` | Exact trust manifest ref. | Manifest presence is not execution authority. |
| `version_ref` | Exact reviewed version ref. | Version drift makes the grant stale. |
| `actor_ref` | Exact reviewer/operator actor ref. | Actor ref is safe metadata only. |
| `approval_ref` | Exact approval ref. | Missing or placeholder approval refs are denied. |
| `scope_ref` | Exact scope ref. | Overbroad or missing scope is denied. |
| `capability_refs` | One or more exact declared capability refs. | Unlisted capabilities are not granted. |
| `requested_grant_refs` | One or more requested grant refs. | Requested grants do not grant authority by themselves. |
| `grant_status` | `granted`, `revoked`, `stale`, or `blocked`. | Only `granted` plus current staleness can be considered active metadata. |
| `staleness_status` | `current` or `stale`. | Stale grants cannot be treated as active. |
| `revocation_ref` | Exact revocation ref. | Revocation must be available before a grant is usable. |
| `audit_refs` | One or more audit refs. | Audit refs are summaries only, not raw logs. |
| `receipt_refs` | Optional safe receipt refs. | Receipt refs are safe refs only. |
| `replay_ref` | Replay validation ref. | Replay does not execute extension code. |

The record pins these fields to safe values:

- `exact_scope: true`
- `overbroad_scope: false`
- `runtime_import_enabled: false`
- `execution_enabled: false`
- `connector_writes_enabled: false`
- `shell_execution_enabled: false`
- `network_access_enabled: false`
- `browser_automation_enabled: false`
- `mobile_control_enabled: false`
- `public_distribution_claimed: false`

## Revocation Record

A revocation record must bind exactly to the activation grant, package,
manifest, version, actor, approval, and scope refs. Revocation is inspectable
and audit-bound; it does not unload code, revoke operating-system permissions,
kill processes, mutate connectors, execute plugins, or call external services.

Revocation behavior:

- A matching revocation record changes grant status to `revoked`.
- A revoked grant cannot be treated as active.
- A second record with the same exact binding is treated as a duplicate grant
  attempt and is denied by batch validation.
- A revocation with mismatched package, manifest, version, actor, approval, or
  scope refs is denied.
- Revocation records must preserve safe audit and receipt refs only.

## Denial Cases

The activation grant validator denies:

- overbroad scope
- missing or placeholder approval refs
- duplicate grant refs
- duplicate exact package/manifest/version/actor/scope/capability bindings
- stale grants being treated as active
- revoked grants being treated as active
- any record that flips runtime import, execution, connector writes,
  shell/subprocess, network, browser, mobile, or public distribution flags on

## Relationship to Catalog and Runtime

UAA-P2-049 exposes a read-only inspectable catalog. UAA-P2-050 adds exact-scope
activation and revocation records that can be inspected by later catalog or
operator surfaces. These records do not create a callable catalog and do not
enable runtime import.

Future runtime import or callable execution requires a later accepted scoped
milestone with PolicyEngine, LocalApprovalAuthority, route side-effect
classification, OpenAPI checks, Foundation Gate checks, audit receipts,
rollback, abuse cases, tests, and release evidence.

## Evidence Safety

Grant and revocation evidence must use safe refs and redacted summaries only.
It must not include raw package contents, raw manifest contents, raw local
paths, raw logs, raw prompts, raw responses, raw provider payloads, usernames,
hostnames, serials, environment dumps, credential material, cookies, tokens, or
private content.

## Known Gaps

- UAA-P2-048 static package review for arbitrary packages remains not shipped.
- No callable catalog exists.
- No plugin runtime import exists.
- No package execution exists.
- No connector write, shell/subprocess, network/browser automation, mobile
  control, or public distribution authority exists.
- No persistence-backed activation registry exists.
- MCP/A2A compatibility remains strategy/watchlist only and does not expand
  activation authority.

## Rollback

To roll back UAA-P2-050, remove this document, the activation grant schema, the
activation/revocation record models and validators, activation grant tests,
documentation-integrity checks, manifest capability metadata, product-truth
updates, roadmap/Kanban updates, and docs index/canonical-map links. Runtime
authority does not need rollback because no runtime import, execution,
connector write, shell, network, browser, mobile, or distribution authority is
added.
