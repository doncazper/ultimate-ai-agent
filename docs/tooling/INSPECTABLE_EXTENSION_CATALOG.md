# Inspectable Extension Catalog

Status: active UAA-P2-049 inspectable extension catalog

Scope: read-only inspection behavior for extension metadata. The catalog is a
safe-ref view over repo-owned extension trust records and blocked/unknown
candidate states. It is separate from any callable catalog and does not install,
import, execute, activate, revoke, fetch, mutate, or distribute extension
packages.

Canonical schema:

```text
docs/schemas/inspectable_extension_catalog.schema.json
```

Canonical API:

```text
GET /extensions/catalog
```

The route returns a `ResultEnvelope` containing
`uaa_inspectable_extension_catalog.v1` data. It is read-only, validation-only,
blocked from production authority, and covered by OpenAPI route metadata.

## Catalog Model

The catalog root includes:

- `catalog_ref`
- `catalog_status: read_only_inspection`
- `read_only: true`
- `inspectable_catalog_enabled: true`
- `progressive_disclosure_enabled: true`
- `metadata_first_index_enabled: true`
- `callable_catalog_enabled: false`
- `automatic_instruction_loading_enabled: false`
- `full_instruction_auto_load_enabled: false`
- `hidden_skill_activation_enabled: false`
- `skill_runtime_import_enabled: false`
- `external_marketplace_fetch_enabled: false`
- `runtime_import_enabled: false`
- `execution_enabled: false`
- `connector_writes_enabled: false`
- `shell_execution_enabled: false`
- `network_access_enabled: false`
- `browser_automation_enabled: false`
- `mobile_control_enabled: false`
- `public_distribution_claimed: false`
- `blocked_capabilities`
- `compact_skill_index_refs`
- `progressive_disclosure_refs`
- `docs_refs`
- `schema_refs`
- `safe_summary`
- `developer_guidance_refs`
- `final_hardening_refs`

Each catalog entry includes:

| Field | Meaning | Safety boundary |
|---|---|---|
| Package identity | Safe package, version, publisher, and kind refs. | Identity is not install, import, or execution authority. |
| Compact skill metadata | Safe compact skill index and metadata summary refs. | Metadata can be inspected before any full instruction review. |
| Provenance | Safe source, review, license refs, and reviewed/blocked/unknown status. | Unknown or blocked provenance keeps the entry inactive. |
| Hashes | Safe file refs, SHA-256 values when reviewed, and reviewed/missing/unknown status. | Raw package content and raw local paths are not returned. |
| Declared capabilities | Safe capability refs, kind, risk, and safe purpose. | Capabilities are inspectable only and not callable. |
| Risk | Highest catalog risk class. | High or critical risk cannot become active through the catalog. |
| Activation status | `inactive`, `blocked`, `revoked`, or `future_scoped`. | There is no `active` status in this milestone. |
| Blocked/unknown state | `blocked`, `unknown`, or `future_scoped` with blocker refs. | Fail closed and keep inactive. |
| Requested grants | Safe grant request refs and blocked/future-scoped status. | Requested grants do not grant authority. |
| Audit refs | Safe review refs. | Audit refs are summaries, not raw logs. |
| Visibility status | Implemented, partial, planned, mock-only, blocked, deprecated, contradicted, or unknown posture. | Visibility is not runtime authority. |
| Trust posture | Reviewed metadata, unknown blocked, blocked by policy, or future review required. | Trust posture only describes inspectable metadata. |
| Callable posture | Inspectable only, blocked runtime, or future exact lane required. | No current catalog entry is callable. |
| Required grant refs | Future grant refs that would be required before runtime behavior. | Required grant refs do not grant authority. |
| Blocked reason | Operator-readable reason the entry cannot execute. | Reasons must use redacted summaries only. |
| Review evidence refs | Safe audit and review refs. | Evidence refs do not expose raw logs or package contents. |
| Safe adoption posture | Repo-owned metadata only, reviewed adaptation required, or blocked until scoped milestone. | Adoption posture is not install or import authority. |
| Progressive disclosure | Metadata-first status, full-instruction load posture, operator-selection requirement, and disabled hidden/automatic loading flags. | Full skill instructions are never auto-loaded and cannot become hidden context or runtime authority. |

## Read-Only Route Behavior

`GET /extensions/catalog` may show:

- declared capabilities
- compact skill index refs
- metadata summary refs
- provenance status
- file hash status and reviewed SHA-256 values
- risk class
- requested grant status
- activation status
- blocked or unknown state
- blocker refs
- audit refs

The route must not expose raw package contents, raw manifest contents, raw local
paths, raw logs, raw prompts, raw responses, raw provider payloads, usernames,
hostnames, serials, environment dumps, credential material, cookies, tokens, or
private content.

## Callable Catalog Separation

The inspectable catalog is not a callable catalog. A catalog entry remains
non-callable even when provenance, file hashes, declared capabilities, or audit
refs are present.

Callable/runtime catalog behavior remains not scoped:

- no plugin install
- no plugin enablement
- no plugin runtime import
- no skill runtime import
- no arbitrary plugin execution
- no connector writes
- no shell/subprocess execution
- no unrestricted network or browser automation
- no mobile control
- no autonomous background execution
- no public distribution claim
- no production authority claim
- no automatic full instruction loading
- no hidden skill activation
- no external marketplace fetch

## OpenAPI Impact

UAA-P2-049 adds exactly one read-only OpenAPI path:

```text
GET /extensions/catalog
```

The path belongs to the extension-catalog route group, has no production
runtime side effects, and remains blocked from production authority by default.
There is no corresponding POST, apply, enable, import, execute, activate,
revoke, fetch, install, or connector-write route.

## Relationship to UAA-P1-024, UAA-P2-048, and UAA-P2-050

UAA-P1-024 defines the trust boundary and trust-manifest schema. UAA-P2-049
adds the read-only catalog surface over safe metadata and blocked/unknown
states.

UAA-P2-048 static package review remains not complete in this patch. The
catalog can show hash/provenance status, but it does not claim a complete
static package review pipeline for arbitrary packages.

UAA-P2-050 adds exact-scope activation and revocation records in
`docs/tooling/EXTENSION_ACTIVATION_GRANTS.md` and
`docs/schemas/extension_activation_grant.schema.json`. The catalog can cite
those safe refs, but `GET /extensions/catalog` still cannot create, accept,
revoke, enforce, or execute activation grants.

UAA-P2-051 adds a strategy/watchlist-only MCP/A2A compatibility document in
`docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`. The catalog does not expose
MCP/A2A runtime support, connector writes, plugin execution, broad tool
invocation, or network authority.

UAA GoatCitadel catch-up Phase 09 adds final ecosystem posture fields and CLI
inspection in `docs/control_center/UAA_GOATCITADEL_CATCHUP_EXTENSIBILITY_FINAL.md`
and `scripts/dev/uaa_extensions.py inspect-catalog`. This is still read-only
catalog metadata; plugin runtime import remains blocked, connector writes
remain blocked, and production authority remains blocked.

Hermes Runtime Adoption Phase 13 adds progressive skill disclosure posture in
`docs/runtime/UAA_HERMES_RUNTIME_PROGRESSIVE_SKILL_DISCLOSURE.md`. The catalog
now exposes compact skill index refs, metadata summary refs, operator-selected
full-instruction posture, blocked automatic instruction loading, blocked hidden
activation, blocked skill runtime import, and blocked marketplace fetch. It
does not add a new route, package install, runtime import, executable skill
enablement, hidden context injection, provider/model call, connector write, or
production authority.

## Known Gaps

- Static package review for arbitrary packages remains scoped to UAA-P2-048.
- Runtime activation and revocation execution remain not scoped; UAA-P2-050
  ships record-only activation and revocation contracts.
- No callable catalog exists.
- No runtime import or package execution exists.
- No automatic full-instruction loading or hidden skill activation exists.
- No marketplace fetch or external package import exists.
- No persistence-backed extension registry exists.
- MCP/A2A compatibility remains watchlist-only.

## Rollback

To roll back UAA-P2-049, remove the `GET /extensions/catalog` route, the
extension catalog core model/builder, the catalog schema, this document,
catalog tests, route-count updates, and documentation-integrity/OpenAPI
references. Runtime authority does not need rollback because no execution,
import, connector write, shell, network, browser, mobile, or distribution
authority is added.
