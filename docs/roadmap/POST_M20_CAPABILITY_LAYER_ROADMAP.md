# Post-M20 Capability Layer Roadmap

Status: Active roadmap projection maintained through v0.26.1. M21 and M22 are implemented/released contract-only; M22 is safety-hardened; M23-M40 remain planned/provisional.

M14-M20 remain implemented/released through reviewed milestones. v0.25.0 / M21 is implemented/released as OpenWebUI Bridge + Chat Shell Integration Contract only. v0.26.0 / M22 is implemented/released as Local Model Runtime Activation Contract only, and v0.26.1 hardens M22 verifier precision and metadata key secret hygiene only. M23-M40 are provisional but canonical after v0.18.4 unless superseded by a reviewed roadmap patch.

These milestones are high-level charters, not implementation. Every milestone needs its own implementation prompt and review prompt. Every risky surface gets a hardening patch before the next capability jump.

No implementation is added by this roadmap projection patch.

This roadmap adds no backend API routes, frontend behavior, runtime execution, local model execution, model/provider calls, network calls, remote execution, mobile app code, Android app code, iOS app code, macOS app code, mobile sensor APIs, Device Capability Broker implementation, MCP runtime support, Agent Skills runtime support, AGENTS.md runtime loading, sandbox execution, tool execution, browser automation, Computer Use, plugin enablement, dependencies, or architecture behavior changes.

## Sequence

| Version | Milestone | Title | Status |
| --- | --- | --- | --- |
| v0.25.0 | M21 | OpenWebUI Bridge + Chat Shell Integration Contract | implemented/released contract-only |
| v0.26.0 | M22 | Local Model Runtime Activation Contract | implemented/released contract-only; hardened by v0.26.1 |
| v0.27.0 | M23 | First Real Local LLM Call, Non-Tool, Non-Authoritative | planned/provisional |
| v0.27.1 | Hardening | Local LLM Call Hardening | planned/provisional |
| v0.28.0 | M24 | Memory Provider Abstraction + Local Memory Store | planned/provisional |
| v0.28.1 | Hardening | Memory Safety Hardening | planned/provisional |
| v0.29.0 | M25 | Truth Source Router + Evidence Claim Checker | planned/provisional |
| v0.30.0 | M26 | Tool Execution Sandbox Contract, Dry-Run Only | planned/provisional |
| v0.31.0 | M27 | MCP / Agent Skills / AGENTS.md Trust Registry, Quarantine-Only | planned/provisional |
| v0.32.0 | M28 | Local Sandbox Backend Abstraction | planned/provisional |
| v0.33.0 | M29 | First Low-Risk Tool Dry-Run + Approval Preview | planned/provisional |
| v0.34.0 | M30 | First Approved Low-Risk Local Tool Execution | planned/provisional |
| v0.35.0 | M31 | CCC Native Client Contract: iOS / Android / macOS | planned/provisional |
| v0.36.0 | M32 | Device Pairing + Trust Handshake Contract | planned/provisional |
| v0.37.0 | M33 | Mobile Approval Surface Prototype, No Sensors | planned/provisional |
| v0.38.0 | M34 | macOS Local Companion Contract / Prototype | planned/provisional |
| v0.39.0 | M35 | Device Capability Broker Implementation, No Sensors Yet | planned/provisional |
| v0.40.0 | M36 | Mobile Capture Inbox, Selected Input Only | planned/provisional |
| v0.41.0 | M37 | One Governed Sensor Capability | planned/provisional |
| v0.42.0 | M38 | Browser Automation Contract, No Execution | planned/provisional |
| v0.43.0 | M39 | Observability Export Adapters | planned/provisional |
| v0.44.0 | M40 | Agent Evaluation + Regression Harness | planned/provisional |

## Narrative

M21 starts with OpenWebUI bridge contracts only, preserving Python Agent Core authority. v0.25.0 implements that contract/planning/validation layer without OpenWebUI integration, deployment config, backend route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority. v0.26.0 implements M22 local runtime activation contracts as metadata-only validation, and v0.26.1 hardens M22 verifier precision plus metadata key secret hygiene. No model was called, no runtime was activated, and no endpoint was contacted. M23 remains planned/provisional for the first bounded local LLM call without tools, memory writes, external network, or authority claims. The v0.27.1 hardening patch must label model output as non-authoritative and prevent secret echo or tool-call leakage.

M24 and M25 introduce memory and truth governance after provenance, delete/export, and claim evidence rules are explicit. Memory remains recall. Model claims remain inspectable and must not become source of truth.

M26-M30 move from sandbox contracts to dry-run previews and only then to a first explicitly approved low-risk local tool. Tool execution must remain local, reversible where practical, receipt-backed, and blocked from network, credentials, browser/computer-use, or irreversible actions at first.

M31-M37 define CCC native client contracts, pairing, mobile approval surfaces, macOS companion planning, the Device Capability Broker, selected capture, and one governed sensor capability. Native client and sensor work must not bypass approvals, consent, receipts, redaction, or Python Agent Core authority.

M38-M40 add browser automation contracts, observability exports, and agent evaluation/regression harnesses. Browser automation remains no-execution at M38, and observability/evals arrive before higher autonomy.

## Read Before Future Prompts

Future implementation prompts after M20 must read:

- `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.
- `docs/roadmap/ECOSYSTEM_WATCHLIST.md`.
- `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md`.

M21 is implemented/released by v0.25.0 as contract-only. M22 is implemented/released by v0.26.0 as contract-only and hardened by v0.26.1. M23-M40 remain planned/provisional.
## M19 Baseline Note

v0.23.0 / M19 is implemented as Mobile Companion Contract/API Planning only.
It did not implement M20 Device Capability Broker. Device Capability Broker is
required before sensors. v0.24.0 now implements M20 as contract-only planning
and validation. M19 added no mobile app, Android app, iOS app, native build
workflow, OS permission integration, or mobile sensor access. Capture cannot
silently become memory.
Phone/mobile is not the agent brain.

v0.23.1 is a cleanup/hardening patch for M19 roadmap status and mobile contract
safety tests only. It adds no Device Capability Broker implementation, mobile
app, Android app, iOS app, macOS app, native build workflow, mobile sensor
access, OS permission integration, background service, notification runtime,
backend API route, dependency, runtime execution, model/provider call, remote
execution, plugin enablement, or production authority.

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. It adds no Device Capability Broker runtime
implementation, mobile app, Android app, iOS app, macOS app, native build
workflow, mobile sensor access, OS permission integration, background service,
notification runtime, backend API route, dependency, runtime execution,
model/provider call, remote execution, plugin enablement, OpenWebUI
integration, or production authority. M21 is implemented/released
contract-only by v0.25.0. M22 is implemented/released contract-only by
v0.26.1. M23-M40 remain planned/provisional.
