# Post-M20 Capability Layer Roadmap

Status: Active roadmap projection maintained through v0.37.3. M21 and M22 are implemented/released contract-only; M23 is implemented/released manual fixed-prompt local call only and hardened by v0.27.1; M24 is implemented/released as governed memory provider/local store, hardened by v0.28.1, and docs-cleaned by v0.28.2; M25 is implemented/released contract-only and hardened by v0.29.1 and v0.29.2; M26 is implemented/released as deterministic grounded recall/context-pack contracts and hardened by v0.30.1; M27 is implemented/released as validation-only Tool Broker v2 contracts; v0.31.1 is docs-only baseline normalization; M28 is implemented/released as Approval Authority v2 + Action Policy Expansion and hardened by v0.32.1; M29 is implemented/released as Agent Task Planning Engine; M30 is implemented/released as Multi-Step Execution Framework state-machine-only contracts and hardened by v0.34.1; M31 is implemented/released as Real Tool Runtime Adapter, Single Safe No-Op Tool and hardened by v0.35.1 for no-op runtime adapter safety; M32 is implemented/released as Safe Local Filesystem Metadata Tool and hardened by v0.36.1; M33 is implemented/released as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1; v0.37.2 adds local developer launcher tooling only; v0.37.3 repairs active M34 roadmap label alignment and documentation-integrity coverage only; M34-M40 remain planned/provisional.

M14-M20 remain implemented/released through reviewed milestones. v0.25.0 / M21 is implemented/released as OpenWebUI Bridge + Chat Shell Integration Contract only. v0.26.0 / M22 is implemented/released as Local Model Runtime Activation Contract only, and v0.26.1 hardens M22 verifier precision and metadata key secret hygiene only. v0.27.0 / M23 is implemented/released as manual/CLI-only, loopback-only, fixed-prompt-only, non-tool, and non-authoritative. v0.27.1 hardens M23 endpoint-label safety, approval evidence checks, response redaction/caps, CLI guardrails, policy docs, static verification, Foundation Gate criteria, and Foundation Gate report atomic write/replace safety. v0.28.0 / M24 is implemented/released as governed, reviewed-write-only local memory provider/store foundation. v0.28.1 repairs and hardens the M24 memory contract without expanding authority. v0.28.2 removes a duplicate roadmap status row only and adds no capability. v0.29.0 / M25 is implemented/released as deterministic, local, contract-only Truth Source Router + Evidence Claim Checker. v0.29.1 hardens M25 unknown/arbitrary truth ref denial only. v0.29.2 hardens local-dev API authority and raw preview safety only. v0.30.0 / M26 is implemented/released as deterministic Grounded Recall Router + Evidence-Linked Context Pack Builder contracts, v0.30.1 hardens source_ref/source_kind consistency, v0.31.0 / M27 is implemented/released as validation-only Tool Broker v2 + Safe Tool Intent Contracts, v0.31.1 normalizes the GitHub README polish commit into a docs-only baseline, v0.32.0 / M28 is implemented/released as Approval Authority v2 + Action Policy Expansion, v0.32.1 hardens evaluator revalidation for raw/secret action inputs, v0.33.0 / M29 is implemented/released as Agent Task Planning Engine, v0.34.0 / M30 is implemented/released as Multi-Step Execution Framework, v0.34.1 hardens M30 safety, v0.35.0 / M31 is implemented/released as Real Tool Runtime Adapter, Single Safe No-Op Tool, v0.36.0 / M32 is implemented/released as Safe Local Filesystem Metadata Tool, v0.36.1 hardens M32 filesystem metadata path safety, v0.37.0 / M33 is implemented/released as First Safe Local File Read Proposal, Redacted Preview Only, v0.37.1 hardens M33 redacted preview safety, v0.37.2 adds local developer launcher tooling only, and v0.37.3 repairs active M34 roadmap label alignment and documentation-integrity coverage only. M34-M40 are provisional but canonical after v0.37.3 unless superseded by a reviewed roadmap patch.

These milestones are high-level charters, not implementation. Every milestone needs its own implementation prompt and review prompt. Every risky surface gets a hardening patch before the next capability jump.

No implementation is added by this roadmap projection patch.

This roadmap adds no backend API routes, frontend behavior, runtime execution, local model execution, model/provider calls, network calls, remote execution, mobile app code, Android app code, iOS app code, macOS app code, mobile sensor APIs, Device Capability Broker implementation, MCP runtime support, Agent Skills runtime support, AGENTS.md runtime loading, sandbox execution, tool execution, browser automation, Computer Use, plugin enablement, dependencies, or architecture behavior changes.

## Sequence

| Version | Milestone | Title | Status |
| --- | --- | --- | --- |
| v0.25.0 | M21 | OpenWebUI Bridge + Chat Shell Integration Contract | implemented/released contract-only |
| v0.26.0 | M22 | Local Model Runtime Activation Contract | implemented/released contract-only; hardened by v0.26.1 |
| v0.27.0 | M23 | First Real Local LLM Call, Non-Tool, Non-Authoritative | implemented/released manual-only |
| v0.27.1 | Hardening | Local LLM Call Hardening | implemented/released hardening-only |
| v0.28.0 | M24 | Memory Provider Abstraction + Local Memory Store | implemented/released |
| v0.28.1 | M24 hardening | Contract Repair + Memory Safety Hardening | implemented/released |
| v0.28.2 | Docs cleanup | Duplicate roadmap row cleanup | implemented/released docs-only |
| v0.29.0 | M25 | Truth Source Router + Evidence Claim Checker | implemented/released contract-only |
| v0.29.1 | M25 hardening | Reject Unknown Truth Refs | implemented/released hardening-only |
| v0.29.2 | M25 hardening | Local Dev API Authority + Raw Preview Safety | implemented/released hardening-only |
| v0.30.0 | M26 | Grounded Recall Router + Evidence-Linked Context Pack Builder | implemented/released contract-only |
| v0.30.1 | M26 hardening | Recall Source Ref / Source Kind Consistency | implemented/released |
| v0.31.0 | M27 | Tool Broker v2 + Safe Tool Intent Contracts | implemented/released |
| v0.31.1 | Docs normalization | GitHub README Polish Baseline Normalization | implemented/released docs-only |
| v0.32.0 | M28 | Approval Authority v2 + Action Policy Expansion | implemented/released contract-only |
| v0.32.1 | M28 hardening | Evaluator Revalidation for Raw/Secret Action Inputs | implemented/released hardening-only |
| v0.33.0 | M29 | Agent Task Planning Engine | implemented/released contract-only |
| v0.34.0 | M30 | Multi-Step Execution Framework | implemented/released contract-only |
| v0.34.1 | M30 hardening | Execution State Machine, Replay, and No-Side-Effect Safety | implemented/released |
| v0.35.0 | M31 | Real Tool Runtime Adapter, Single Safe No-Op Tool | implemented/released |
| v0.35.1 | M31 hardening | No-Op Tool Runtime Adapter Safety | implemented/released |
| v0.36.0 | M32 | Safe Local Filesystem Metadata Tool | implemented/released |
| v0.36.1 | M32 hardening | Filesystem Metadata Path Safety | implemented/released hardening-only |
| v0.37.0 | M33 | First Safe Local File Read Proposal, Redacted Preview Only | implemented/released |
| v0.38.0 | M34 | Broader File Capability Review | planned/provisional |
| v0.39.0 | M35 | Device Capability Broker Implementation, No Sensors Yet | planned/provisional |
| v0.40.0 | M36 | Mobile Capture Inbox, Selected Input Only | planned/provisional |
| v0.41.0 | M37 | One Governed Sensor Capability | planned/provisional |
| v0.42.0 | M38 | Browser Automation Contract, No Execution | planned/provisional |
| v0.43.0 | M39 | Observability Export Adapters | planned/provisional |
| v0.44.0 | M40 | Agent Evaluation + Regression Harness | planned/provisional |

## Narrative

M21 starts with OpenWebUI bridge contracts only, preserving Python Agent Core authority. v0.25.0 implements that contract/planning/validation layer without OpenWebUI integration, deployment config, backend route, frontend feature, runtime execution, user-content local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority. v0.26.0 implements M22 local runtime activation contracts as metadata-only validation, and v0.26.1 hardens M22 verifier precision plus metadata key secret hygiene. v0.27.0 implements M23 as a manual fixed-prompt local model call path with local approval validation, fake-transport tests/gates, no tools, no memory writes, no backend route, no OpenWebUI runtime bridge, no Control Center execution control, and non-authoritative output. v0.27.1 hardens secret echo checks, endpoint-label safety, forged approval resistance, response caps/redaction, CLI guardrails, policy docs, verifier/Gate coverage, and Foundation Gate report atomic write/replace safety without changing runtime behavior.

M24 introduces governed local memory provider/store foundation after provenance, delete/export, and source priority rules are explicit. Memory remains recall, not authority, and memory is not ground truth. v0.29.0 implements M25 truth source routing and evidence claim checking as deterministic local contracts over provided refs only; it adds no web search, external verification, model/provider calls, source fetching, retrieval/RAG/vector/embedding behavior, memory writes, evidence mutation, backend routes, dependencies, or production authority.

M26 is implemented/released as Grounded Recall Router + Evidence-Linked Context Pack Builder contracts only. It adds deterministic local planning over provided safe candidates, safe summary-only context packs, and no context injection runtime, vector search, embeddings, external retrieval, memory write, backend route, dependency, or production authority.

M32 is implemented/released as one safe local filesystem metadata tool under server-owned safe roots. M33 is implemented/released as one bounded redacted file preview proposal tool under server-owned safe roots. It does not add raw file output, full-file read output, content hashes, directory listing, traversal, mutation, backend raw-file/execute routes, arbitrary tools, context injection, dependencies, or production authority. M34-M40 remain planned/provisional; future broader file, native-client, device, browser, observability, and evaluation work must not bypass approvals, consent, receipts, redaction, or Python Agent Core authority.

M38-M40 add browser automation contracts, observability exports, and agent evaluation/regression harnesses. Browser automation remains no-execution at M38, and observability/evals arrive before higher autonomy.

## Read Before Future Prompts

Future implementation prompts after M20 must read:

- `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.
- `docs/roadmap/ECOSYSTEM_WATCHLIST.md`.
- `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md`.

M21 is implemented/released by v0.25.0 as contract-only. M22 is implemented/released by v0.26.0 as contract-only and hardened by v0.26.1. M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only and hardened by v0.27.1. M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2. M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine. M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only. M34-M40 remain planned/provisional.
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
v0.26.1. M23 is implemented/released by v0.27.0 as manual fixed-prompt local
call only and hardened by v0.27.1. M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2. M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine. M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only. M34-M40 remain planned/provisional.
