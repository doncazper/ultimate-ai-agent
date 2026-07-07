# Governed Product Pilot Authority Profile

Status: implemented local pilot profile, not production authority
Baseline: v0.104.0 / 0.104.0

The Governed Product Pilot profile moves UAA from a mostly blocked shell toward
a usable local-first product pilot without deleting the sealed/default hard
rules. The default profile remains `sealed` and deny-by-default. The pilot
profile is an exact-lane profile: each promoted local lane must prove Python
Core ownership, approval binding where execution-capable, idempotency, audit
receipt, rollback or safe-disable posture, redaction, tests, and CLI/API/Core
parity.

## Backend Truth

- Core contract: `src/ultimate_ai_agent/core/runtime_gateway/governed_product_pilot_profile.py`
- API read route: `GET /api/runtime/governed-product-pilot-profile`
- CLI inspection: `scripts/dev/uaa_runtime.py authority-profile`
- Portable evidence CLI:
  `scripts/dev/uaa_runtime.py export-evidence-envelope --json` and
  `scripts/dev/uaa_runtime.py verify-evidence-envelope --profile --json`
- Verifier: `scripts/verify_governed_product_pilot_authority_profile.py`
- Focused tests: `tests/test_governed_product_pilot_authority_profile.py`

Control Center may display or initiate backend-owned envelopes for exact lanes,
but it does not mint authority. Product behavior cannot live only in React
state.

## Exact Pilot Lanes

| Lane | Profile status | What is promoted | Boundary |
|---|---|---|---|
| Live local agent runtime | Implemented | Configured loopback/local RuntimeGateway calls with non-authoritative output, redacted receipts, and safe refs. | No remote provider/model calls, tools, memory writes, file writes, connector writes, browser automation, or production authority. |
| Mature action execution | Implemented | Named RuntimeGateway authority capabilities: one read-only local status command under `workspace/read` and exact Action Inbox approved focused pytest, repo-verifier, frontend-check, and repo-doctor command execution under active `workspace/execute` AuthorityLease scope. | No generic tool execution, arbitrary shell/subprocess, networked commands, installs, background execution, or approval refs as authority. |
| Portable evidence envelopes | Profile-ready | Local hash-signed receipt envelopes with safe refs, hash refs, timestamp, policy decision, approval ref, action id, side-effect class, and verifier version. | No public notarization claim, persisted signing key material, raw payloads, raw logs, raw local paths, provider payloads, or sensitive material. |
| Durable orchestration | Implemented | Local run records, checkpoints, progress refs, approval-wait states, retry/recovery posture, cancellation/blocked states, receipt refs, evidence refs, and redacted errors. | No broad background autonomy, scheduler authority, remote execution, provider/tool dispatch, or production authority. |

## Capability Maturity Matrix

| Capability | Current maturity | Evidence | Remaining gap |
|---|---|---|---|
| Mature action execution | Strong exact-lane local pilot | RuntimeGateway allowlist, AuthorityLease evaluation, Action Inbox approval envelope, receipt refs, CLI/API/Core parity, and tests for read-only command plus exact approved focused pytest, repo-verifier, frontend-check, and repo-doctor execution. | More action lanes require separate domain/capability scope, approval binding, rollback/safe-disable, redaction, and verifier coverage. |
| Signed portable evidence | Strong local hash envelope, not public notarization | Envelope includes receipt, evidence, action, policy, approval, side-effect, timestamp, verifier, deterministic hash ref, local signed-envelope ref, offline verifier, tamper tests, redaction tests, and CLI export/verify. | Public signing, key custody, revocation, external notarization, and cross-device trust remain blocked until a separate signing-boundary milestone. |
| Durable orchestration | Strong local durable run posture | Profile binds local run records, checkpoints, approval wait, retry/recovery, cancel/blocked/dead-letter posture, read-model status refs, redacted errors, and marks durable event log as truth while progress refs are not truth. | Live resume/cancel/retry execution controls and scheduler/background workers remain blocked until exact lanes are approved. |
| Live local agent runtime | Usable local pilot lane | RuntimeGateway supports configured loopback/local model receipts with non-authoritative output, safe refs, redaction posture, and sealed/local-runtime/operator-approved profile separation. | Remote provider calls, arbitrary model routing, tool dispatch, memory writes, and production authority remain blocked. |

## Portable Evidence Verification

The pilot uses a deterministic local hash envelope instead of persisted signing
keys. This is portable offline verification for local governance evidence, not
public notarization.

```bash
scripts/dev/uaa_runtime.py export-evidence-envelope --json
scripts/dev/uaa_runtime.py verify-evidence-envelope --profile --json
scripts/dev/uaa_runtime.py verify-evidence-envelope --input <local-envelope-json> --json
```

The verifier checks required fields, envelope hash, signed-envelope hash chain,
redaction posture, missing fields, and tamper detection. The CLI accepts a local
input file for offline verification but does not echo or persist the local path.

## Still Blocked

- Broad autonomy.
- Unrestricted shell/subprocess execution.
- Browser automation.
- Connector writes.
- Remote execution.
- Plugin runtime import.
- Production authority.
- Public beta, public release, or public distribution claims.
- Raw prompt, response, provider payload, log, local path, account material,
  credential material, or private-data persistence.

## Promotion Rule

Future promotion must be lane-specific. A new exact lane needs scope,
PolicyEngine/LocalApprovalAuthority binding where relevant, idempotency,
receipts, rollback or safe-disable posture, redaction, CLI/API/Core parity,
route side-effect classification, OpenAPI/API manifest alignment, focused
tests, verifier coverage, product-language truth, and operator-visible blocked
states. Graduation of one lane does not unlock the broader capability class.

## Next Exact Promotion Prompts

Use these prompts only after the current profile is green:

- Portable signing boundary: "Promote Governed Product Pilot portable evidence
  from deterministic local hash envelopes to an exact local signing-key
  boundary. Preserve sealed default, add key provenance refs, rotation/revocation
  refs, offline verifier parity, tamper/redaction tests, and no public
  notarization or production claim."
- Additional action authority capability: "Add one named RuntimeGateway action
  capability with argv-only scope, cwd jail if command-like, timeout, env scrub,
  exact LocalApprovalAuthority binding, idempotency, receipt,
  rollback/safe-disable, redaction, CLI/API/Core parity, and route
  classification."
- Durable run controls: "Promote one durable orchestration control, such as
  cancel or resume, as an exact lane over existing run refs with approval
  binding where effectful, idempotency, receipt refs, replay posture, redacted
  errors, CLI/API/Core parity, and tests."
- Live runtime expansion: "Promote one additional local-runtime invocation lane
  only through RuntimeGateway with configured endpoint matching, output as
  non-authoritative evidence, cost/latency/status refs, approval before side
  effects, redaction, safe-disable, and no remote provider or production
  authority."
