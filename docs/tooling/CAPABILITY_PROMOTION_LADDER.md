# Capability Promotion Ladder

Status: active capability governance contract

This ladder is the shared promotion model for MCP, A2A, browser automation,
providers, connectors, CRM writes, email/calendar, shell, memory writes, and
future background work. It is a contract and review vocabulary only. It does
not add runtime authority, connector writes, provider/model calls, browser
automation, shell/subprocess execution, memory writes, public distribution, or
production authority.

## Ladder

| Stage | Meaning | Required proof |
|---|---|---|
| Declared | A capability is named as a possible future integration. | Safe ref, owner/ref, non-goal statement, blocked authority refs. |
| Discovered | Metadata is inspected without trusting it. | Provenance ref, schema refs, transport/auth posture, no raw payloads. |
| Imported as UAA Capability Candidate | External metadata is converted into UAA's capability language. | `CapabilityManifest` or equivalent Python Core contract with authority, side-effect, risk, privacy, cost, receipt, revocation, and safe-disable metadata. |
| Classified | Policy-facing risk is explicit. | Side-effect class, risk level, credential posture, approval requirement, rollback posture, blocked states. |
| Preview/Dry-run | The operator can inspect what would happen. | No side effects, no runtime dispatch, safe argument refs, expected evidence/receipt refs. |
| Policy checked | UAA evaluates whether selection/execution is allowed. | `PolicyEngine` decision refs, blocked reason codes, no model/provider output authority. |
| Exact approval bound | Human approval matches the exact scope. | LocalApprovalAuthority or lane-specific exact approval binding for capability/tool refs, argument refs, credential refs, budget refs, expiry, revocation, and expected receipts. |
| Broker-invoked | A UAA-owned broker performs the action. | Later scoped milestone only; direct React/model/provider/tool self-invocation remains blocked. |
| Receipted | The result or block is durable and reviewable. | Safe summary, redacted input/output refs, approval/policy refs, receipt ref, rollback/refusal details. |
| Replayable | A reviewer can reconstruct why it happened or why it blocked. | Audit/ref chain, selection ref, policy decision ref, approval decision ref, receipt ref, no re-execution. |
| Revocable | Future use can be disabled or invalidated. | Revocation refs, kill-switch/safe-disable posture where applicable, stale grant denial. |

## Default Stance

Unknown capability metadata is blocked and review-required. Unknown does not mean read-only.
Manifest presence, model output, provider output, remote
metadata, memory recall, plugin metadata, or UI state cannot authorize work.

Promotion must be exact-scoped and reversible. A later stage may not be claimed
until the earlier stages have source-controlled contracts, focused tests,
redacted receipts/evidence, docs, and rollback or safe-disable posture.

## Cross-Capability Use

MCP and A2A use this ladder to prevent protocol metadata from becoming direct
agent authority. Browser automation uses it to keep observe, dry-run, and
click/form/auth/download/upload lanes separate. Providers and billing use it to
bind exact provider/model/credential/cost refs before any invocation. Connectors,
CRM writes, email/calendar, shell, memory writes, and background work must use
the same declared-to-revocable progression before any runtime authority is
promoted.
