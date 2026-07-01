# UAA A2A Gateway Foundation

Status: implemented as metadata/import contracts only

This milestone promotes A2A from watchlist-only planning into a UAA-owned
gateway foundation. It does not add remote dispatch, peer-auth runtime,
gRPC/HTTP execution, public agent-card discovery, remote approvals, connector
writes, remote tool invocation, browser/shell execution, provider/model calls,
public distribution, or production authority.

## Product Stance

Good path:

```text
Agent proposes delegation intent
-> Planner selects an A2A capability candidate
-> Authority Engine checks scope
-> Approval Engine binds exact approval
-> Capability Broker may invoke a future exact-scoped adapter
-> Receipt Ledger records allowed or blocked result
-> Evaluator decides next step
```

Bad path:

```text
Remote agent card appears
-> Model or UI delegates to the remote agent
-> Remote agent does work or self-approves
```

The current foundation implements only the contracts needed for the good path
up to blocked/proposal posture. It does not implement the invocation step.

## Implemented Contracts

`src/ultimate_ai_agent/core/capabilities/a2a_gateway.py` defines:

- A2A agent-card metadata with safe refs for agent identity, card identity,
  owner, schema version, declared capabilities, requested grants, endpoint
  posture, provenance, status, audit, replay, revocation, safe-disable, and
  receipt refs.
- A2A trust, auth, and activation posture enums.
- A2A-to-UAA capability candidate import.
- Spec-shaped A2A 1.0 Agent Card fixture parsing into safe refs only,
  including `supportedInterfaces`, protocol binding/version metadata, provider
  metadata, capabilities, security posture, modes, skills, and signatures.
- Proposal-only handoff envelopes.
- Exact delegation approval-binding contracts.
- Blocked receipt contracts.
- Replay/audit records.

`CapabilityRegistry.manifest_from_a2a_agent_card()` imports existing
`UAAA2AAgentCardMetadataImport` records through those contracts. The legacy
`A2AAgentCardMinimal` Python name remains only as a temporary internal alias
for that UAA-local metadata import shim. It is not an official A2A protocol
Agent Card. The resulting `CapabilityManifest` is an A2A capability candidate,
not a callable remote agent.

`A2AAgentCardV1` parses official-shaped A2A 1.0 Agent Card fixtures for
compatibility tests only. `a2a_v1_agent_card_to_metadata()` converts that shape
into UAA-owned safe refs and redacted metadata; it does not fetch well-known
cards, select transports, authenticate peers, call JSON-RPC/HTTP/gRPC methods,
or dispatch work.

## Blocked-By-Default Posture

Unknown A2A agent-card metadata is blocked / review required. Unknown does not mean read-only,
and it does not mean delegation-safe.

Imported A2A candidates require `a2a:reviewed` scope and
`a2a_exact_delegation_approval_required`. The default manifest allows reviewer
and human-gate coordination only. It deliberately does not allow
`agent_as_tool`, live handoff, remote dispatch, peer-auth runtime, remote
self-approval, memory writes, provider calls, connector writes, browser/shell
execution, or direct React/model/provider invocation.

Endpoint URLs, raw card payloads, credentials, raw task text, raw status text,
raw prompts, raw responses, raw local paths, logs, usernames, hostnames,
environment dumps, cookies, tokens, and provider payloads must not be durable
evidence. Use safe refs and redacted summaries only.

## Approval Boundary

Approval refs are identifiers only until validated. A future exact approval
must match both metadata and an explicit approval context:

- exact agent ref
- exact card ref
- exact UAA capability id
- exact task ref from `A2AExactDelegationApprovalContext`
- exact handoff ref from `A2AExactDelegationApprovalContext`
- exact requested grant refs
- exact credential refs when required
- exact expiration ref from `A2AExactDelegationApprovalContext`
- exact expected receipt ref
- exact revocation ref

Mismatches produce blocked decisions. Remote agents cannot approve their own
delegation, and remote status output is not truth authority.

## Receipt And Replay

Every blocked A2A delegation attempt can produce a safe receipt with:

- receipt ref
- capability id
- agent ref
- card ref
- blocked reason codes
- safe summary
- approval ref or approval-missing ref
- redacted task/status refs
- audit ref
- replay ref
- rollback/safe-disable ref

Replay records let a reviewer reconstruct selection, policy, approval, receipt,
and revocation refs without re-delegating or executing remote work.

## Capability Promotion Ladder

A2A follows `docs/tooling/CAPABILITY_PROMOTION_LADDER.md`:

```text
Declared
-> Discovered
-> Imported as UAA Capability Candidate
-> Classified
-> Preview/Dry-run
-> Policy checked
-> Exact approval bound
-> Broker-invoked
-> Receipted
-> Replayable
-> Revocable
```

This PR reaches metadata import, classification, proposal-only preview,
approval-binding checks, blocked receipts, replay, and revocation refs. It does
not reach broker invocation.

## Future Lanes

Near-term A2A work should stay local and inspectable:

- richer fixture agent-card examples
- read-only CLI inspection of imported card posture
- task/handoff review queues
- remote-worker compatibility mapping
- stale card/version drift checks
- revocation and kill-switch UI/CLI inspection

Later lanes may consider exact-scoped local/loopback handoff adapters only
after policy, LocalApprovalAuthority binding, receipt storage, replay,
redaction, OpenAPI/API manifest posture, and safe-disable plans are accepted.

## Non-Goals

This foundation does not add:

- remote A2A dispatch
- peer-auth runtime
- gRPC or HTTP execution
- public agent-card discovery
- remote approvals
- remote self-approval
- connector writes
- remote tool invocation
- browser or shell execution
- provider/model calls
- live delegation
- backend routes
- public beta, public release, public distribution, or production authority

## Verification

Focused proof lives in:

- `tests/test_a2a_gateway_foundation.py`
- `scripts/verify_a2a_gateway_foundation.py`
- existing `tests/test_a2a_adapter_boundaries.py`

The verifier checks that source, tests, docs, product-language guardrails, and
watchlist language preserve the no-new-authority posture.
