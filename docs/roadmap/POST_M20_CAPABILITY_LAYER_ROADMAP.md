# Post-M20 Capability Layer Roadmap

Status: Active roadmap projection maintained through v0.50.0.

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
M47-M60 remain planned/provisional.
M34 is implemented/released as planning/docs/verifier
only. M35 is implemented/released as Safe File Review Workflow Contracts. M36 is implemented/released as CCC File Review Surface, Review-Only. M37 is implemented/released as Review Approval Capture, Review-Only Persistence. M38 is implemented/released as Safe Context Proposal From Approved Review. M39 is implemented/released as CCC Context Proposal Surface. M40 is implemented/released as Context Handoff Approval, No Injection. M41 is implemented/released as Local Prototype Safety Freeze. M42 is implemented/released as Mobile Companion Product Contract Refresh. M43 is implemented/released as Mobile API Boundary, Read-Only. M44 is implemented/released as CCC iOS Skeleton, No Authority. M45 is implemented/released as CCC iOS Local Read-Only Connection. M46 is implemented/released as iOS Review/Receipt Read-Only Surfaces. M43 is the first mobile
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
| v0.51.0 | M47 | TestFlight Pipeline, Internal Only | planned/provisional |
| v0.52.0 | M48 | First Internal TestFlight Build | planned/provisional |
| v0.53.0 | M49 | Mobile Review Approval Capture | planned/provisional |
| v0.54.0 | M50 | Mobile Approval Audit Hardening | planned/provisional |
| v0.55.0 | M51 | OpenWebUI Bridge Adapter Pilot | planned/provisional |
| v0.56.0 | M52 | OpenWebUI Safe Conversation Surface | planned/provisional |
| v0.57.0 | M53 | Controlled Tool Expansion Review | planned/provisional |
| v0.58.0 | M54 | Safe Media Metadata Inspector | planned/provisional |
| v0.59.0 | M55 | Redacted Observability Export | planned/provisional |
| v0.60.0 | M56 | Agent Eval Regression Harness | planned/provisional |
| v0.61.0 | M57 | Runtime Sandbox Architecture Review | planned/provisional |
| v0.62.0 | M58 | Dry-Run Execution Audit Harness | planned/provisional |
| v0.63.0 | M59 | Public GitHub Readiness | planned/provisional |
| v0.64.0 | M60 | Local Developer Beta Freeze | planned/provisional |

## Prompt-Pack Strategy

Recommended next prompt after v0.50.0:

```text
v0.51.0 / M47 - TestFlight Pipeline, Internal Only
```

The next prompt pack is M47 TestFlight Pipeline, Internal Only.

Extra-hard reviews are required for M37, M38, M40, M47, M48, M49, M51, M52,
M57, and M58. Mandatory hardening is expected by default for M35-M40, M43-M50,
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
