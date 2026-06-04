# M34-M60 Roadmap Supersession

Status: Active roadmap source of truth through v0.38.0.

v0.38.0 implements M34 Broader File Capability Review as planning,
architecture review, documentation, verifier, and Foundation Gate work only.
The v0.37.4 supersession remains the historical patch that replaced the older
active M35-M40 projection. v0.38.0 adds no runtime file capability, backend
route, frontend runtime feature, dependency, file-review workflow implementation,
approval capture, context proposal, context injection, memory write, export,
mobile app, TestFlight pipeline, execution authority, or production authority.

## Supersession Rule

Active milestone prompts after v0.37.4 must use the sequence below. Archived
release packets and older roadmap snapshots remain historical evidence, not the
active source of truth. If another document disagrees with this page, this page
and the canonical roadmap win until a later reviewed roadmap patch supersedes
them.

M34 is implemented/released as planning/docs/verifier only. M35 is the first
implementation milestone after this supersession and review. M42 resumes mobile planning. M44 is the first iOS
skeleton milestone. M47 is the TestFlight-capable pipeline milestone. M48 is the
first internal TestFlight build milestone. M49 and M50 are the first meaningful
mobile approval capture and audit milestones.

## Sequence

| Version | Milestone | Title | Status | Scope |
| --- | --- | --- | --- | --- |
| v0.38.0 | M34 | Broader File Capability Review | implemented/released planning/docs/verifier only | Planning, docs, verifier, Foundation Gate, boundary matrix, risk register, decision record, and M35 readiness only |
| v0.39.0 | M35 | Safe File Review Workflow Contracts | planned/provisional | Contract-only file review workflow, review packet, and no-authority approval boundary |
| v0.40.0 | M36 | CCC File Review Surface, Review-Only | planned/provisional | Read-only/review-only CCC surface for redacted review packets |
| v0.41.0 | M37 | Review Approval Capture, Review-Only Persistence | planned/provisional | Governed review approval capture with audit-only persistence |
| v0.42.0 | M38 | Safe Context Proposal From Approved Review | planned/provisional | Proposal contracts only; no automatic context injection |
| v0.43.0 | M39 | CCC Context Proposal Surface | planned/provisional | Review-only CCC surface for context proposals |
| v0.44.0 | M40 | Context Handoff Approval, No Injection | planned/provisional | Approval boundary for handoff decisions; no injection |
| v0.45.0 | M41 | Local Prototype Safety Freeze | planned/provisional | Freeze and review local prototype safety before mobile work |
| v0.46.0 | M42 | Mobile Companion Product Contract Refresh | planned/provisional | Mobile planning refresh only; no native app implementation |
| v0.47.0 | M43 | Mobile API Boundary, Read-Only | planned/provisional | Read-only mobile API boundary contract |
| v0.48.0 | M44 | CCC iOS Skeleton, No Authority | planned/provisional | First iOS skeleton; no authority, sensors, or production workflow |
| v0.49.0 | M45 | CCC iOS Local Read-Only Connection | planned/provisional | Local read-only connection only |
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

Recommended next prompt after v0.38.0:

```text
v0.39.0 / M35 - Safe File Review Workflow Contracts
```

The first three prompt packs after this patch are:

1. M35 Safe File Review Workflow implementation/review/hardening.
2. M36 CCC File Review Surface implementation/browser-smoke review/hardening.
3. M37 Review Approval Capture review-only persistence.

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
