# M34-M60 Roadmap Supersession

Status: Active roadmap source of truth through v0.49.0.

v0.38.0 implements M34 Broader File Capability Review as planning,
architecture review, documentation, verifier, and Foundation Gate work only.
The v0.37.4 supersession remains the historical patch that replaced the older
active M35-M40 projection. v0.38.0 adds no runtime file capability, backend
route, frontend runtime feature, dependency, file-review workflow implementation,
approval capture, context proposal, context injection, memory write, export,
mobile app, TestFlight pipeline, execution authority, or production authority.
v0.38.2 repairs active current-baseline labels and documentation-integrity
coverage after the v0.38.1 Yellow review. v0.39.0 implements M35 Safe File
Review Workflow Contracts as contract-only, review-only logic over
already-redacted preview results. v0.39.1 hardens exact file/path binding for
M35 approvals. v0.40.0 implements M36 CCC File Review Surface, Review-Only as
a frontend-only display surface. v0.40.1 hardens M36 read-only surface safety.
v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence as
safe-ref-only approval and denial capture bound to exact redacted review
packets. v0.42.0 implements M38 Safe Context Proposal From Approved Review as
proposal-only, non-authoritative contracts from exact-scope approved redacted
file review records. v0.43.0 implements M39 CCC Context Proposal Surface as a
frontend-only review surface. v0.44.0 implements M40 Context Handoff Approval,
No Injection as contract-only approval decisions with exact proposal binding.
v0.45.0 implements M41 Local Prototype Safety Freeze as a docs/verifier/Gate
safety freeze before mobile work resumes. v0.46.0 implements M42 Mobile Companion Product Contract Refresh as planning/docs/contracts/verifier work only. v0.47.0 implements M43 Mobile API Boundary, Read-Only as contract-only boundary work. v0.48.0 implements M44 CCC iOS Skeleton, No Authority as source-only, mock-only, read-only, non-authoritative SwiftUI skeleton work. v0.48.1 hardens the M44 verifier allowance for that reviewed source-only skeleton. v0.49.0 implements M45 CCC iOS Local Read-Only Connection as local-only, loopback-only, read-only contract/status work with no runtime network call.

## Supersession Rule

Active milestone prompts after v0.37.4 must use the sequence below. Archived
release packets and older roadmap snapshots remain historical evidence, not the
active source of truth. If another document disagrees with this page, this page
and the canonical roadmap win until a later reviewed roadmap patch supersedes
them.

M34 is implemented/released as planning/docs/verifier only. M35 is
implemented/released as contract-only Safe File Review Workflow Contracts and
hardened by v0.39.1 for exact file/path binding. M36 is
implemented/released as frontend-only CCC File Review Surface, Review-Only and
hardened by v0.40.1 for read-only surface safety.
M37 is implemented/released. M38 is implemented/released. M39 is implemented/released. M40 is implemented/released. M41 is implemented/released. M42 is implemented/released. M43 is implemented/released. M44 is implemented/released. M45 is implemented/released. M46-M60 remain planned/provisional. M42 resumes mobile planning. M44 is the first iOS
skeleton milestone. M47 is the TestFlight-capable pipeline milestone. M48 is the
first internal TestFlight build milestone. M49 and M50 are the first meaningful
mobile approval capture and audit milestones.

## Sequence

| Version | Milestone | Title | Status | Scope |
| --- | --- | --- | --- | --- |
| v0.38.0 | M34 | Broader File Capability Review | implemented/released planning/docs/verifier only | Planning, docs, verifier, Foundation Gate, boundary matrix, risk register, decision record, and M35 readiness only |
| v0.39.0 | M35 | Safe File Review Workflow Contracts | implemented/released contract-only | Contract-only file review workflow, review packet, and no-authority approval boundary |
| v0.39.1 | M35 hardening | File Review Exact File/Path Binding | implemented/released hardening | Exact file_ref and safe_path_ref binding, model_copy denial, verifier and Foundation Gate hardening |
| v0.40.0 | M36 | CCC File Review Surface, Review-Only | implemented/released frontend-only | Read-only/review-only CCC surface for redacted review packets |
| v0.40.1 | M36 hardening | CCC File Review Surface Read-Only Safety | implemented/released hardening | Safe-ref-only display and no-mutating-request guard |
| v0.41.0 | M37 | Review Approval Capture, Review-Only Persistence | implemented/released | Governed review approval capture with audit-only persistence |
| v0.42.0 | M38 | Safe Context Proposal From Approved Review | implemented/released contract-only | Proposal contracts only; no automatic context injection |
| v0.43.0 | M39 | CCC Context Proposal Surface | implemented/released frontend-only | Review-only CCC surface for context proposals |
| v0.44.0 | M40 | Context Handoff Approval, No Injection | implemented/released contract-only | Approval boundary for handoff decisions; no injection |
| v0.45.0 | M41 | Local Prototype Safety Freeze | implemented/released safety freeze | Freeze and review local prototype safety before mobile work |
| v0.46.0 | M42 | Mobile Companion Product Contract Refresh | implemented/released contract refresh | Mobile planning refresh only; no native app implementation |
| v0.47.0 | M43 | Mobile API Boundary, Read-Only | implemented/released contract-only | Read-only mobile API boundary contract |
| v0.48.0 | M44 | CCC iOS Skeleton, No Authority | implemented/released source-only | First iOS skeleton; no authority, sensors, or production workflow |
| v0.48.1 | M44 hardening | CCC iOS Skeleton Verifier Allowance | implemented/released hardening | Narrow verifier allowance for reviewed source-only iOS skeleton files |
| v0.49.0 | M45 | CCC iOS Local Read-Only Connection | implemented/released contract/status-only | Local read-only connection only |
| v0.50.0 | M46 | iOS Review/Receipt Read-Only Surfaces | planned/provisional | Read-only review and receipt surfaces |
| v0.51.0 | M47 | TestFlight Pipeline, Internal Only | planned/provisional | Internal-only pipeline; no public distribution or production authority |
| v0.52.0 | M48 | First Internal TestFlight Build | planned/provisional | First internal build with explicit review gates |
| v0.53.0 | M49 | Mobile Review Approval Capture | planned/provisional | Mobile review approval capture; no execution authority |
| v0.54.0 | M50 | Mobile Approval Audit Hardening | planned/provisional | Hardening and audit coverage for mobile approvals |
| v0.55.0 | M51 | OpenWebUI Bridge Adapter Pilot | planned/provisional | Pilot adapter boundary; no authority bypass |
| v0.56.0 | M52 | OpenWebUI Safe Conversation Surface | planned/provisional | Safe conversation surface with Python Agent Core authority |
| v0.57.0 | M53 | Controlled Tool Expansion Review | planned/provisional | Planning/review only for future tool expansion |
| v0.58.0 | M54 | Safe Media Metadata Inspector | planned/provisional | Metadata-only media inspection; no creative authority |
| v0.59.0 | M55 | Redacted Observability Export | planned/provisional | Redacted export contracts only |
| v0.60.0 | M56 | Agent Eval Regression Harness | planned/provisional | Evaluation regression harness |
| v0.61.0 | M57 | Runtime Sandbox Architecture Review | planned/provisional | Architecture review only |
| v0.62.0 | M58 | Dry-Run Execution Audit Harness | planned/provisional | Dry-run audit harness; no execution authority |
| v0.63.0 | M59 | Public GitHub Readiness | planned/provisional | Public readiness review/docs only |
| v0.64.0 | M60 | Local Developer Beta Freeze | planned/provisional | Local beta freeze and safety review |

## Prompt-Pack Strategy

Recommended next prompt after v0.49.0:

```text
v0.50.0 / M46 - iOS Review/Receipt Read-Only Surfaces
```

The first prompt packs after this patch are:

1. M41 Local Prototype Safety Freeze is implemented/released by v0.45.0.
2. M42 Mobile Companion Product Contract Refresh is implemented/released by v0.46.0.
3. M43 Mobile API Boundary, Read-Only is implemented/released by v0.47.0.
4. M44 CCC iOS Skeleton, No Authority is implemented/released by v0.48.0.

Extra-hard reviews are required for M37, M38, M40, M47, M48, M49, M51, M52,
M57, and M58. Mandatory hardening is expected by default for M35-M40, M43-M50,
M51-M52, and M54-M58. Docs/planning-only milestones are M34, M42, M53, M57, and
M59. Browser smoke review belongs in M36, M39, M41, M45-M46, and M51-M52. Mobile
simulator/device testing belongs only in M44-M50 and only after explicit native
tooling approval.

## Safety Boundaries Through M60

Through M60, the following remain blocked unless a later reviewed roadmap patch
explicitly changes the boundary and adds implementation, tests, verifiers,
Foundation Gate coverage, and release review:

- arbitrary raw file browsing
- arbitrary caller-selected filesystem roots
- raw file export
- full-file reads
- arbitrary shell/subprocess
- unrestricted network tools
- provider/model calls as authority
- background workers
- mobile sensors
- plugin enablement
- production authority
- unreviewed memory writes
- automatic context injection
- raw prompt/provider payload exposure
- external SaaS/analytics SDKs
- credentials/cookie handling
- remote execution
- browser automation execution
- approval refs as authority

## Media And Color Placement

Media Color Pipeline work is not core before M60 except for M54 Safe Media
Metadata Inspector. OCIO deterministic transform preview belongs after M60
unless media-safe file contracts mature sooner through reviewed roadmap work.
AI gamut expansion is much later, experimental, preview-only, creative,
non-authoritative, never default, and never truth recovery.
