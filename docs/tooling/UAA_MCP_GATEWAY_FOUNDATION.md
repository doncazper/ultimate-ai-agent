# UAA MCP Gateway Foundation

Status: MCP metadata/import foundation

This milestone promotes MCP from watchlist-only planning into an inspectable
UAA-owned gateway foundation. It does not add MCP runtime calls, `tools/call`,
server subprocess start, network transport, OAuth flow execution, secret
resolution, connector writes, provider/model calls, browser automation, public
marketplace claims, public distribution, or production authority.

MCP is an interoperability layer. UAA remains the governed operating system.
Discovered MCP tools, resources, and prompts become UAA capability candidates
only after Python Agent Core imports and classifies their metadata.

## Product Posture

Good path:

```text
Agent proposes intent
-> Planner selects candidate capability
-> Authority/Policy checks scope
-> Approval binding validates exact refs
-> Future Capability Broker invokes only in a later scoped lane
-> Receipt Ledger records result or block
-> Replay/Audit reconstructs the decision
```

Blocked path:

```text
Agent sees MCP tool
-> Agent calls MCP tool
-> Tool does thing
```

The blocked path remains unavailable. React, model output, provider output,
plugin metadata, and MCP metadata cannot call MCP directly.

## Current Implementation

Python Core now defines MCP gateway metadata contracts in
`src/ultimate_ai_agent/core/capabilities/mcp_gateway.py`:

- `McpDiscoveryToolMetadata` captures server/tool refs, schemas, provenance,
  transport posture, auth posture, activation posture, side-effect posture,
  risk, privacy, cost, credential refs, audit refs, replay refs, revocation
  refs, safe-disable refs, expected receipt refs, and blocked authority refs.
- `mcp_tool_metadata_to_capability_candidate()` imports MCP-shaped metadata
  into a `CapabilityManifest` candidate.
- `build_mcp_preview_contract()` creates a no-side-effect preview contract.
- `McpExactApprovalBinding`, `McpExactApprovalContext`, and
  `evaluate_mcp_exact_approval_binding()` define exact approval matching for
  future MCP work.
- `build_mcp_blocked_receipt()` records blocked attempts using safe refs.
- `build_mcp_replay_audit_record()` reconstructs why selection, policy,
  approval, and receipt posture blocked or would later allow work.

Existing `CapabilityRegistry.manifest_from_mcp_tool_spec()` now fails closed:
unreviewed MCP metadata imports as blocked/review-required candidate metadata,
not as read-only authority.

## Required Default

Unknown MCP tool means:

```text
blocked / review required
```

Unknown MCP tool does not mean:

```text
read-only
```

Unreviewed MCP imports require `mcp:reviewed` policy scope and exact approval
binding before any future runtime lane could proceed. This milestone still does
not register an adapter or invoke MCP.

## Capability Promotion Ladder Binding

MCP follows `docs/tooling/CAPABILITY_PROMOTION_LADDER.md`:

1. Declared: MCP concept is named with non-goals and blocked authority refs.
2. Discovered: metadata is inspected as untrusted safe refs.
3. Imported as UAA Capability Candidate: metadata becomes a `CapabilityManifest`.
4. Classified: side-effect, risk, authority, cost, privacy, credential, and
   receipt posture are explicit.
5. Preview/Dry-run: UAA can describe what would be needed without doing it.
6. Policy checked: `PolicyEngine` blocks missing review scope.
7. Exact approval bound: approval must match server/tool/capability refs,
   credential refs when required, expected receipt and revocation refs, and the
   argument/scope/budget/expiry refs supplied by `McpExactApprovalContext`.
8. Broker-invoked: future only; no broker invocation exists in this milestone.
9. Receipted: blocked attempts produce redacted safe-ref receipts.
10. Replayable: audit records reconstruct selection/policy/approval/receipt.
11. Revocable: revocation and safe-disable refs are part of the candidate.

## Blocked Authority

The following remain blocked:

- MCP runtime invocation
- generic `tools/call`
- MCP server subprocess start
- external network transport
- OAuth flow execution
- secret resolution or raw credential handling
- connector writes
- provider/model calls
- browser automation
- React direct MCP calls
- model/provider direct MCP calls
- public marketplace claims
- public distribution
- production authority

## Staged MCP Roadmap

Near-term safe lanes:

- read-only and fixture/dry-run capabilities only
- local file/resource inspection through safe refs
- calendar/email read contracts, not writes
- CRM fixture provider
- provider catalog inspection
- documentation/search index resources
- local deterministic workers
- no-op/dry-run action previews

Later lanes, each requiring separate exact-scoped promotion:

- connector reads
- exact-approved low-risk writes
- scoped recurring workflows
- background execution
- broader external integrations

## Verification

Focused proof:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_gateway_foundation.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_mcp_gateway_foundation.py
```

Broader proof:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry.py tests/test_capability_registry_coordinator.py -q
git diff --check
```

This proof is metadata/contract-only. It cannot be cited as callable MCP
runtime support.
