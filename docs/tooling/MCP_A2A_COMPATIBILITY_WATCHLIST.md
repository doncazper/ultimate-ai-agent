# MCP/A2A Compatibility Watchlist

Status: active UAA-P2-051 MCP/A2A compatibility watchlist

Scope: strategy/watchlist only for future Model Context Protocol (MCP) and
agent-to-agent (A2A) compatibility planning, with links to accepted
metadata/import foundation docs. MCP has a metadata/import foundation in
`docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md`; A2A has a metadata/import foundation in
`docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md`. This document records concepts,
risks, future gates, open questions, and likely manifest/capability
implications before any runtime authority exists.

This watchlist does not imply MCP/A2A support is shipped. It also does not
imply callable MCP/A2A support is shipped. The MCP and A2A foundations are
metadata/import only: unknown MCP tools and unknown A2A agents are blocked and
review-required, not read-only or delegation-ready. They add no runtime
authority, no connector writes, no plugin execution, no broad tool invocation,
no remote dispatch, and no network authority. They do not add backend routes,
OpenAPI paths, runtime imports, package execution, model/provider authority,
shell/subprocess execution, browser automation, mobile control, autonomous
background execution, public distribution, or production authority.
The short import rule remains: treat unknown MCP tools as blocked and unknown
A2A agents as blocked until reviewed.

Related ecosystem docs:

```text
docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md
docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
docs/tooling/EXTENSION_ACTIVATION_GRANTS.md
docs/tooling/CAPABILITY_PROMOTION_LADDER.md
docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md
docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
docs/capability_registry.md
```

## MCP Concepts

MCP-style ecosystems commonly describe external tools, resources, prompts,
sampling surfaces, server identity, transport details, and client/server
capability negotiation. For UAA planning, those concepts can only be considered
as metadata until a later scoped milestone approves an adapter.

Planning refs that may be useful later:

- server identity ref
- tool/resource/prompt declaration refs
- capability declaration refs
- transport boundary ref
- authentication posture ref
- provenance and package review refs
- side-effect and risk classification refs
- audit and replay refs

## A2A Concepts

A2A-style ecosystems commonly describe agent identity, agent cards, task or
handoff envelopes, capability discovery, status exchange, and delegation
contracts. UAA now models these as local safe-ref metadata, capability
candidates, proposal-only handoff envelopes, exact approval-binding contracts,
blocked receipts, and replay/audit refs. They remain non-delegating metadata
until a later exact-scoped runtime lane is accepted.

Planning refs that may be useful later:

- agent identity ref
- agent card ref
- delegation contract ref
- task envelope ref
- safe status summary ref
- authority boundary ref
- approval and revocation refs
- receipt, audit, and replay refs

## Risks

| Risk | Why it matters | Required stance now |
|---|---|---|
| Hidden authority | Tool, resource, server, or agent metadata can look callable even when no review has happened. | Treat all MCP/A2A metadata as inspectable only. |
| Connector writes | External connectors could mutate remote systems if granted too broadly. | Keep connector writes unavailable until exact scoped approval exists. |
| Broad tool invocation | A generic tool bridge can bypass capability-level risk review. | Require per-capability manifests and side-effect classes. |
| Network authority | MCP/A2A transports may require network access, authentication, redirects, or streaming. | Keep network authority unavailable until a later reviewed transport milestone. |
| Plugin execution | Some integrations package executable code or runtime imports. | Keep plugin execution and runtime import disabled. |
| Credential exposure | Connector/server/agent setup can tempt raw tokens, cookies, paths, logs, or env dumps into evidence. | Use safe refs and redacted summaries only. |
| Delegation drift | A2A handoff output can be mistaken for UAA authority. | Keep PolicyEngine and LocalApprovalAuthority as the governing authorities. |
| Contract drift | External protocol versions can change faster than local gates. | Add compatibility review and Foundation Gate checks before support claims. |

## Required Future Gates

Any future MCP or A2A implementation milestone must define and verify all of
the following before support can be claimed:

| Gate | Required proof before implementation |
|---|---|
| Scope gate | Exact protocol subset, transport, surfaces, risk ceiling, and non-goals. |
| Policy gate | PolicyEngine evaluation for every declared capability or delegation path. |
| Approval gate | LocalApprovalAuthority or successor exact approval binding for mutating, external, high-risk, credential-bearing, or delegation behavior. |
| Side-effect gate | Route side-effect classification and capability side-effect classes. |
| Manifest gate | Manifest fields for identity, provenance, hashes, declared capabilities, requested grants, risk class, activation status, revocation, audit refs, and safe summaries. |
| Transport gate | Explicit network/browser/connector boundary; no implicit external transport. |
| Credential gate | Credential refs only, with no raw credential material in evidence. |
| Evidence gate | Safe refs, redacted summaries, receipt refs, audit refs, and replay refs only. |
| OpenAPI gate | OpenAPI checks for any new API surface, with stable operation IDs and route metadata. |
| Foundation Gate | Foundation Gate checks proving no bypass of policy, approval, redaction, side-effect, or route-contract requirements. |
| Revocation gate | Exact-scope revocation model that prevents stale or revoked grants from being treated as active. |
| Rollback gate | Operator rollback and safe-disable plan before any runtime enablement. |
| Test gate | Focused tests for missing approval, overbroad scope, unsafe metadata, denied runtime authority, redaction, duplicate requests, stale grants, revoked grants, and blocked/unknown states. |

No future gate may treat model/provider output, remote agent output, MCP server
metadata, A2A agent-card metadata, approval refs alone, or manifest presence as
production authority.

## Compatibility Questions

- Which MCP tool/resource/prompt fields map cleanly to UAA declared capability
  refs without creating a callable catalog?
- Which MCP transport assumptions are incompatible with loopback-first,
  disabled-by-default operation?
- How should MCP server identity, package provenance, and per-file hashes bind
  to extension trust manifests?
- Which A2A agent-card fields are safe to expose in an inspectable catalog?
- How should A2A delegation envelopes bind to durable run records, audit refs,
  receipt refs, and replay refs?
- Which protocol features require network authority, connector writes,
  streaming, credential refs, runtime import, or background execution and must
  remain blocked until separately scoped?
- How should version drift, stale manifests, revoked grants, and unknown
  provenance be represented without implying shipped support?
- What route metadata and OpenAPI operation IDs would be required if a future
  read-only inspection API is approved?

## Manifest/Capability Implications

Likely future manifest/capability fields, if a later milestone scopes them:

| Field | Planning purpose | Current status |
|---|---|---|
| `protocol_family_ref` | Distinguish MCP, A2A, local extension, or connector metadata. | Watchlist only. |
| `protocol_version_ref` | Track reviewed compatibility version. | Watchlist only. |
| `transport_boundary_ref` | Record loopback, local file, remote, browser, or connector transport assumptions. | Watchlist only. |
| `declared_capability_refs` | Map protocol capabilities to local declared capability refs. | Inspectable metadata only. |
| `side_effect_class_ref` | Bind tools/resources/delegations to read, preview, write, external, or high-risk classes. | Future gate. |
| `requested_grant_refs` | Record requested activation or delegation grants. | Existing grant records are non-runtime. |
| `credential_ref_required` | Mark whether a future adapter would need credential refs. | Future gate. |
| `revocation_ref` | Bind activation/delegation to revocation. | Existing revocation records are non-runtime. |
| `audit_ref` | Preserve review and decision evidence by safe ref. | Safe-ref only. |
| `replay_ref` | Support future replay validation without raw payloads. | Safe-ref only. |

These fields would extend inspection and review. They do not create runtime
execution, connector writes, network access, or delegation authority.

## Non-Goals

UAA-P2-051 does not add:

- MCP runtime authority
- A2A runtime authority
- connector writes
- plugin execution or runtime import
- broad tool invocation
- network authority
- browser automation
- shell/subprocess execution
- mobile control
- autonomous background execution
- model/provider output as authority
- backend routes or OpenAPI paths
- public distribution or production authority

## Evidence Safety

Compatibility evidence must use safe refs and redacted summaries only. It must
not include raw prompts, raw responses, raw provider payloads, raw local paths,
raw logs, usernames, hostnames, serials, environment dumps, credential
material, cookies, tokens, raw connector payloads, raw protocol payloads, or
private content.

## Rollback

To roll back UAA-P2-051, remove this watchlist, documentation-integrity checks,
docs index and canonical-map links, product-truth/Kanban/roadmap updates, and
ecosystem-watchlist references added for this task. Runtime authority does not
need rollback because this task adds no MCP/A2A runtime, no connector writes,
no plugin execution, no broad tool invocation, and no network authority.
