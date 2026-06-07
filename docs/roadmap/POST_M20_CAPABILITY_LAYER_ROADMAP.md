# Post-M20 Capability Layer Roadmap

Status: Active roadmap projection maintained through v1.5.0.

v0.38.0 implements M34 Broader File Capability Review as planning,
architecture review, documentation, verifier, and Foundation Gate work only.
It adds no backend API route, frontend runtime behavior, runtime execution,
local model execution, model/provider call, network call, remote execution,
mobile app code, iOS app code, Android app code, macOS app code, mobile sensor
API, Device Capability Broker runtime, MCP runtime support, Agent Skills
runtime, AGENTS.md runtime loading, sandbox execution, tool execution, browser
automation, Computer Use, plugin enablement, dependency, architecture behavior
change, raw file read, file review workflow implementation, approval capture,
context injection, memory write, export, or production authority.

No integration is added. No dependency is added. v0.40.0 implements M36 CCC
File Review Surface, Review-Only as frontend-only display over already-redacted
review packets. v0.40.1 hardens M36 read-only surface safety. v0.41.0
implements M37 Review Approval Capture, Review-Only Persistence as safe-ref-only
approval and denial capture for exact redacted review packets. v0.42.0
implements M38 Safe Context Proposal From Approved Review as proposal-only,
non-authoritative contracts from exact-scope approved redacted file review
records. v0.43.0 implements M39 CCC Context Proposal Surface as frontend-only
display. v0.44.0 implements M40 Context Handoff Approval, No Injection as
contract-only approval decisions with exact proposal binding.

M21-M40 are implemented/released through dedicated reviewed milestones.
M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze.
M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh.
M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only.
M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority.
v0.48.1 hardens the M44 verifier allowance for the reviewed source-only iOS skeleton.
M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection.
M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces.
M47 is implemented/released by v0.51.0 as TestFlight Pipeline, Internal Only.
M48 is implemented/released by v0.52.0 as First Internal TestFlight Build.
M49 is implemented/released by v0.53.0 as Mobile Review Approval Capture.
M50 is implemented/released by v0.54.0 as Mobile Approval Audit Hardening.
M51 is implemented/released by v0.55.0 as OpenWebUI Bridge Adapter Pilot.
M52 is implemented/released by v0.56.0 as OpenWebUI Safe Conversation Surface.
M53 is implemented/released. M54 is implemented/released. M55 is implemented/released. M56 is implemented/released. M57 is implemented/released. M58 is implemented/released. M59 is implemented/released as Public GitHub Readiness and M60 is implemented/released as Local Developer Beta Freeze.
M34 is implemented/released as planning/docs/verifier
only. M35 is implemented/released as Safe File Review Workflow Contracts. M36 is implemented/released as CCC File Review Surface, Review-Only. M37 is implemented/released as Review Approval Capture, Review-Only Persistence. M38 is implemented/released as Safe Context Proposal From Approved Review. M39 is implemented/released as CCC Context Proposal Surface. M40 is implemented/released as Context Handoff Approval, No Injection. M41 is implemented/released as Local Prototype Safety Freeze. M42 is implemented/released as Mobile Companion Product Contract Refresh. M43 is implemented/released as Mobile API Boundary, Read-Only. M44 is implemented/released as CCC iOS Skeleton, No Authority. M45 is implemented/released as CCC iOS Local Read-Only Connection. M46 is implemented/released as iOS Review/Receipt Read-Only Surfaces. M47 is implemented/released as TestFlight Pipeline, Internal Only. M48 is implemented/released as First Internal TestFlight Build. M49 is implemented/released as Mobile Review Approval Capture. M50 is implemented/released as Mobile Approval Audit Hardening. M59 is implemented/released as Public GitHub Readiness with no GitHub push, release automation, wiki automation, artifact upload, credential handling, network access, backend route, dependency, production authority, or M60 implementation. M43 is the first mobile
read-only API boundary in this new sequence. M44 is the first iOS skeleton milestone.
M45 is the first local read-only iOS connection contract/status milestone.
M47 is the TestFlight-capable pipeline milestone. M48 is the first internal
TestFlight build. M49-M50 are the first meaningful mobile approval capture and
audit milestones.

The detailed post-M33 supersession source of truth is
`docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## Sequence

| Version | Milestone | Title | Status |
| --- | --- | --- | --- |
| v0.25.0 | M21 | OpenWebUI Bridge + Chat Shell Integration Contract | implemented/released contract-only |
| v0.26.0 | M22 | Local Model Runtime Activation Contract | implemented/released contract-only; hardened by v0.26.1 |
| v0.27.0 | M23 | First Real Local LLM Call, Non-Tool, Non-Authoritative | implemented/released manual-only |
| v0.28.0 | M24 | Memory Provider Abstraction + Local Memory Store | implemented/released |
| v0.29.0 | M25 | Truth Source Router + Evidence Claim Checker | implemented/released contract-only |
| v0.30.0 | M26 | Grounded Recall Router + Evidence-Linked Context Pack Builder | implemented/released contract-only |
| v0.31.0 | M27 | Tool Broker v2 + Safe Tool Intent Contracts | implemented/released contract-only |
| v0.32.0 | M28 | Approval Authority v2 + Action Policy Expansion | implemented/released contract-only |
| v0.33.0 | M29 | Agent Task Planning Engine | implemented/released contract-only |
| v0.34.0 | M30 | Multi-Step Execution Framework | implemented/released contract-only |
| v0.35.0 | M31 | Real Tool Runtime Adapter, Single Safe No-Op Tool | implemented/released |
| v0.36.0 | M32 | Safe Local Filesystem Metadata Tool | implemented/released |
| v0.37.0 | M33 | First Safe Local File Read Proposal, Redacted Preview Only | implemented/released |
| v0.38.0 | M34 | Broader File Capability Review | implemented/released planning/docs/verifier only |
| v0.39.0 | M35 | Safe File Review Workflow Contracts | implemented/released contract-only |
| v0.39.1 | M35 hardening | File Review Exact File/Path Binding | implemented/released hardening |
| v0.40.0 | M36 | CCC File Review Surface, Review-Only | implemented/released frontend-only |
| v0.40.1 | M36 hardening | CCC File Review Surface Read-Only Safety | implemented/released hardening |
| v0.41.0 | M37 | Review Approval Capture, Review-Only Persistence | implemented/released |
| v0.42.0 | M38 | Safe Context Proposal From Approved Review | implemented/released contract-only |
| v0.43.0 | M39 | CCC Context Proposal Surface | implemented/released frontend-only |
| v0.44.0 | M40 | Context Handoff Approval, No Injection | implemented/released contract-only |
| v0.45.0 | M41 | Local Prototype Safety Freeze | implemented/released safety freeze |
| v0.46.0 | M42 | Mobile Companion Product Contract Refresh | implemented/released contract refresh |
| v0.47.0 | M43 | Mobile API Boundary, Read-Only | implemented/released contract-only |
| v0.48.0 | M44 | CCC iOS Skeleton, No Authority | implemented/released source-only |
| v0.48.1 | M44 hardening | CCC iOS Skeleton Verifier Allowance | implemented/released hardening |
| v0.49.0 | M45 | CCC iOS Local Read-Only Connection | implemented/released contract/status-only |
| v0.50.0 | M46 | iOS Review/Receipt Read-Only Surfaces | implemented/released source-only read-only |
| v0.51.0 | M47 | TestFlight Pipeline, Internal Only | implemented/released contract/checklist-only |
| v0.52.0 | M48 | First Internal TestFlight Build | implemented/released reviewed-candidate-only |
| v0.53.0 | M49 | Mobile Review Approval Capture | implemented/released safe-ref-only review capture |
| v0.54.0 | M50 | Mobile Approval Audit Hardening | implemented/released hardening |
| v0.55.0 | M51 | OpenWebUI Bridge Adapter Pilot | implemented/released adapter pilot |
| v0.56.0 | M52 | OpenWebUI Safe Conversation Surface | implemented/released safe conversation surface |
| v0.57.0 | M53 | Controlled Tool Expansion Review | implemented/released |
| v0.58.0 | M54 | Safe Media Metadata Inspector | implemented/released |
| v0.59.0 | M55 | Redacted Observability Export | implemented/released |
| v0.60.0 | M56 | Agent Eval Regression Harness | implemented/released |
| v0.61.0 | M57 | Runtime Sandbox Architecture Review | implemented/released |
| v0.62.0 | M58 | Dry-Run Execution Audit Harness | implemented/released |
| v0.63.0 | M59 | Public GitHub Readiness | implemented/released review-only |
| v0.64.0 | M60 | Local Developer Beta Freeze | implemented/released |
| v0.65.0 | M61 | Autonomy Mode Charter + Authority Levels | implemented/released contract-only |
| v0.66.0 | M62 | Scoped Autonomy Session Contracts | implemented/released contract-only |
| v0.67.0 | M63 | Autonomy Policy Engine v1 | implemented/released contract-only |
| v0.68.0 | M64 | Autonomous Plan Simulator | implemented/released contract-only |
| v0.69.0 | M65 | Autonomy Audit + Replay Viewer | implemented/released contract-only |
| v0.70.0 | M66 | Scoped Approval Bundles | implemented/released contract-only |
| v0.71.0 | M67 | Revocation + Kill Switch | implemented/released contract-only |
| v0.72.0 | M68 | Autonomy Risk Classifier | implemented/released contract-only |
| v0.73.0 | M69 | Low-Risk Autonomous Dry Run | implemented/released contract-only |
| v0.74.0 | M70 | Autonomy Foundation Freeze | implemented/released contract-only |
| v0.75.0 | M71 | Network Tool Contract Review | implemented/released contract-only |
| v0.76.0 | M72 | Read-Only HTTP Fetch Tool, Allowlisted | implemented/released allowlisted/redacted-only |
| v0.77.0 | M73 | Browser Automation Contract Review | implemented/released contract-only |
| v0.78.0 | M74 | Browser Observe-Only Adapter | implemented/released observe-only/redacted-only |
| v0.79.0 | M75 | Browser Action Dry-Run Planner | implemented/released dry-run-only |
| v0.80.0 | M76 | OpenWebUI Runtime Bridge v1 | implemented/released review-only |
| v0.81.0 | M77 | OpenWebUI Safe Handoff Execution | implemented/released exact-bound Agent Core handoff only |
| v0.82.0 | M78 | Plugin Manifest Security Model | implemented/released disabled-only security model |
| v0.83.0 | M79 | Plugin Install Review, Disabled by Default | implemented/released review-only disabled install candidate contracts |
| v0.84.0 | M80 | Network/Browser/OpenWebUI Hardening Freeze | implemented/released freeze-only hardening contracts |
| v0.85.0 | M81 | Runtime Sandbox Spec | implemented/released spec-only |
| v0.86.0 | M82 | Command Proposal Contracts | implemented/released proposal-only |
| v0.87.0 | M83 | Shell Dry-Run Classifier | implemented/released classifier-only |
| v0.88.0 | M84 | Sandboxed Echo/No-Op Command | implemented/released in-process only |

## Prompt-Pack Strategy

Recommended next prompt after v1.5.0:

```text
Run M102 implementation conveyor or M101-M150 active milestone prompt pack.
```

M61 is implemented/released by v0.65.0 as Autonomy Mode Charter + Authority
Levels. M62 is implemented/released by v0.66.0 as Scoped Autonomy Session
Contracts. M63 is implemented/released by v0.67.0 as Autonomy Policy Engine v1.
M64 is implemented/released by v0.68.0 as Autonomous Plan Simulator. M65 is
implemented/released by v0.69.0 as Autonomy Audit + Replay Viewer. M66 is
implemented/released by v0.70.0 as Scoped Approval Bundles. M67 is
implemented/released by v0.71.0 as Revocation + Kill Switch. M68 is
implemented/released by v0.72.0 as Autonomy Risk Classifier. M69 is
implemented/released by v0.73.0 as Low-Risk Autonomous Dry Run. M70 is
implemented/released by v0.74.0 as Autonomy Foundation Freeze. M71 is
implemented/released by v0.75.0 as Network Tool Contract Review. M72 is
implemented/released by v0.76.0 as Read-Only HTTP Fetch Tool, Allowlisted. M73 is
implemented/released by v0.77.0 as Browser Automation Contract Review. M74 is
implemented/released by v0.78.0 as Browser Observe-Only Adapter. M75 is
implemented/released by v0.79.0 as Browser Action Dry-Run Planner. M76 is
implemented/released by v0.80.0 as OpenWebUI Runtime Bridge v1. M77 is
implemented/released by v0.81.0 as OpenWebUI Safe Handoff Execution. M78 is
implemented/released by v0.82.0 as Plugin Manifest Security Model. M79 is
implemented/released by v0.83.0 as Plugin Install Review, Disabled by Default.
M80 is implemented/released by v0.84.0 as Network/Browser/OpenWebUI Hardening
Freeze and currentness-repaired by v0.84.1. M81 is implemented/released by
v0.85.0 as Runtime Sandbox Spec, and M82 is implemented/released by v0.86.0 as
Command Proposal Contracts. M83 is implemented/released by v0.87.0 as Shell
Dry-Run Classifier. M84 is implemented/released by v0.88.0 as Sandboxed
Echo/No-Op Command. M85 is implemented/released by v0.89.0 as Read-Only Command
Allowlist. M86 is implemented/released by v0.90.0 as Shell Approval Gate v1.
M87 is implemented/released by v0.91.0 as Sandboxed Command Audit Replay.
M88 is implemented/released by v0.92.0 as Mutating Command Proposal, No Execution.
M89 is implemented/released by v0.93.0 as Emergency Stop + Process Kill Safety.
M90 is implemented/released by v0.94.0 as Shell/Subprocess Hardening Freeze.
M91 is implemented/released by v0.95.0 as Autonomous Tool Execution Contract.
M92 is implemented/released by v0.96.0 as Low-Risk Tool Autonomy, Single Session.
M93 is implemented/released by v0.97.0 as Multi-Tool Dry-Run to Real Run Promotion.
M94 is implemented/released by v0.98.0 as Autonomous Browser Clicks, Low-Risk
Only. M95 is implemented/released by v0.99.0 as Network Tool Expansion,
Authless Only. M96 is implemented/released by v1.0.0 as Plugin Execution
Sandbox, No External Plugins. M97 is implemented/released by v1.1.0 as
Recurring Automation Contracts. M98 is implemented/released by v1.2.0 as Scoped
Recurring Low-Risk Automation. M99 is implemented/released by v1.3.0 as
Autonomy v1 Safety Freeze. M100 is implemented/released by v1.4.0 as Mobile
Permission Model v1. v1.4.1 adds post-M100 review and promotes M101-M150 as
planned/provisional only in `docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md`.
M101 is implemented/released by v1.5.0 as Mobile Sensor Contract Review.
M102-M150 remain planned/provisional.

Extra-hard reviews are required for M37, M38, M40, M47, M48, M49, M51, M52,
M57, M58, and M59. Mandatory hardening is expected by default for M35-M40, M43-M50,
M51-M52, and M54-M58. Docs/planning-only milestones are M34, M42, M53, M57, and
M59. Browser smoke review belongs in M36, M39, M41, M45-M46, and M51-M52.
Mobile simulator/device testing belongs only in M44-M50 and only after explicit
native tooling approval.

## Through-M60 Safety Boundaries

The following remain blocked through M60 unless a later reviewed roadmap patch
explicitly changes the boundary and adds tests, verifiers, Foundation Gate
coverage, and release review:

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

Media Color Pipeline is not core before M60 except M54 Safe Media Metadata
Inspector. OCIO deterministic transform preview belongs after M60 unless
media-safe file contracts mature through reviewed roadmap work. AI gamut
expansion is later, experimental, preview-only, creative, non-authoritative,
never default, and never truth recovery.
