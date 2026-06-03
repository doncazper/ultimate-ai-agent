# Documentation Integrity Checklist

Status: Active maintenance checklist, v0.28.2

Run this checklist before every release that changes docs, roadmap, API metadata, runtime boundaries, or release status.

## Version Alignment

- `VERSION.md` active baseline matches `pyproject.toml`.
- `VERSION.md` active baseline matches `src/ultimate_ai_agent/__init__.py`.
- `README.md` points to the active `README_IMPORT_vX_Y_Z.md`.
- `README.md` points to the active `ultimate_ai_agent_master_plan_vX_Y_Z.md`.
- active release notes exist.
- active Foundation Gate implementation plan exists.

## Source-of-Truth Hierarchy

- active README/import/master docs identify the current baseline.
- canonical docs are treated as current principle/source-of-truth docs.
- historical release docs remain historical and are not presented as active truth.
- backlog docs are clearly future/not implemented.

## Stale Link Checks

- active README does not point to older import or master plan files.
- active import README includes current key docs.
- active master plan matches current release purpose.
- docs index and canonical map include newly added active docs.
- active tooling governance docs are linked when Codex/plugin policy changes.
- active design governance docs are linked when UI/design policy changes.
- active UI strategy docs are linked when OpenWebUI or CCC client strategy changes.
- active post-M20 roadmap projection docs are linked when long-range sequencing changes.
- roadmap charter docs are linked when milestone sequencing changes.

## Active vs Historical Docs

- historical files are not deleted for ordinary integrity passes.
- older release notes may retain historical version language.
- current docs explain whether features are implemented, simulated, validation-only, dry-run-only, manual-only, planned/disabled, future/backlog, or blocked.

## Safety Claim Checks

- docs do not claim live model/provider/network/runtime execution unless implemented and gated. M23 may describe only the manual/CLI-only, loopback-only, fixed-prompt-only, approval-gated, non-authoritative local call path.
- docs do not claim mobile app, sensor access, OS permission integration, or background service exists unless implemented and gated.
- docs do not claim remote execution, tailnet/private mesh execution, or remote approvals exist unless implemented and gated.
- docs do not claim scanners, Skill Factory, self-improvement, production persistence, or external actions exist unless implemented and gated.
- docs do not claim Codex plugins, plugin installers, native build tools, Xcode workflows, simulators, Chrome authenticated profile control, Computer Use automation, cloud jobs/uploads/training, or deployment workflows are enabled unless explicitly implemented and gated.
- docs do not claim runtime readiness reports, capability matrix entries, or manual smoke reports prove production readiness or authorize execution.
- docs do not claim Control Center production authority, plugin enablement, runtime execution, remote dispatch, model/provider invocation, mobile sensor access, native build control, or production Control Center exists unless implemented and gated.
- docs do not claim design tools, design SaaS sync, UI generators, screenshot-to-code, design-to-code, or automatic design commits are enabled unless implemented and gated.
- docs do not claim OpenWebUI integration, deployment config, plugin/function/tool bridge, native CCC implementation, Android app, iOS app, macOS app, OS permission integration, signing, keystore, App Store workflow, or Play Store workflow exists unless implemented and gated.
- docs do not claim M21-M40 capabilities are implemented unless a dedicated future milestone implements and gates them.
- docs do not claim Device Capability Broker runtime implementation, sensor access, device pairing runtime, mobile storage runtime, backend device routes, or device-client authority exists unless implemented and gated.
- docs do not claim memory provider/local store output is authority, ground truth, automatically written, model-written, OpenWebUI-written, mobile-capture-written, tool-output-written, raw-content-bearing, vector-backed, embedding-backed, cloud-backed, context-injected, production-persistent, or claim-verifying unless a dedicated future milestone implements and gates that behavior.

## Release Note Requirements

- release notes name the release purpose.
- release notes list changed docs/verifiers/gates.
- release notes explicitly state no new runtime powers for docs-only releases.

## Roadmap Update Requirements

- active roadmap names the accepted baseline.
- future milestones remain sequenced.
- future milestone prompts check `docs/roadmap/MILESTONE_CHARTERS.md`.
- future milestone prompts check `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` until superseded by a reviewed roadmap patch.
- M14/M15 sequencing remains explicit: M14 is local backend connection stabilization; M15 is approval queue plus receipt/event viewer UI.
- v0.18.2 design governance remains before M15 and does not implement M15 UI.
- v0.18.3 OpenWebUI/CCC strategy remains before M15 and does not implement M15 UI, OpenWebUI integration, or native clients.
- v0.18.4 post-M20 roadmap projection keeps M21-M40 planned/provisional and does not implement those capabilities.
- v0.19.0 M15 Approval Queue + Receipt/Event Viewer UI is frontend-only, read-only/preview-only, redacted summary-only, and adds no backend route or production authority.
- v0.19.1 M15 Approval/Receipt UI safety hardening is frontend/verifier/Foundation Gate only, keeps OpenAPI path count unchanged, treats approval refs as identifiers only, keeps Python Agent Core as approval authority, and adds no approval execution, approve/deny mutation, M16 timeline, backend route, dependency, or production authority.
- v0.20.0 M16 Event Timeline + Run/Receipt Trace Viewer is frontend-only, read-only, redacted summary-only, uses safe refs/evidence summaries, keeps OpenAPI path count unchanged, and adds no execution, backend route, raw payload display, external telemetry export, dependency, or production authority.
- v0.20.1 M16 trace/redaction safety hardening is frontend/test/verifier/Foundation Gate/docs only, keeps OpenAPI path count unchanged, documents generated build-output hygiene, and adds no M17 viewer, execution, backend route, raw payload display, telemetry export, dependency, or production authority.
- v0.21.0 M17 Evidence/File/Memory Viewer is frontend-only, read-only, redacted summary-only, uses safe refs and memory recall-only summaries, keeps OpenAPI path count unchanged, and adds no file mutation, memory mutation, filesystem browsing, backend route, raw payload display, embedding/vector DB/memory provider implementation, dependency, or production authority.
- v0.21.1 M17 Evidence/File/Memory Viewer safety hardening is frontend/test/verifier/Foundation Gate/docs only, keeps OpenAPI path count unchanged at 74, and adds no M18 surface, backend route, raw payload display, file mutation, memory mutation, filesystem browsing, embedding/vector DB/memory provider implementation, dependency, auth, cookies, analytics, SaaS SDK, or production authority.
- v0.21.2 Developer Environment Command Normalization is dev tooling/docs only, standardizes repo verification on `.venv/bin/python` or Makefile targets, requires no global Python alias, and adds no M18 surface, runtime behavior, frontend behavior, backend route, dependency, network call, model/provider call, mobile/native/browser/computer-use functionality, plugin enablement, or production capability.
- v0.24.0 M20 Device Capability Broker Contract is contract-only planning and validation, keeps OpenAPI path count unchanged at 74, and adds no runtime broker implementation, sensor access, OS permission integration, native clients, pairing runtime, backend API route, dependency, runtime execution, model/provider call, remote execution, plugin enablement, OpenWebUI integration, or production authority.
- v0.25.0 M21 OpenWebUI Bridge + Chat Shell Integration Contract is contract/planning/validation only, keeps OpenAPI path count unchanged at 74, and adds no OpenWebUI integration, deployment config, Docker config, OpenWebUI plugin/function/pipeline/tool/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority.
- v0.25.1 M21 OpenWebUI Bridge Contract Safety Hardening is tests/verifier/Foundation Gate/docs/version only, keeps OpenAPI path count unchanged at 74, scans the OpenWebUI bridge package for forbidden runtime/config fragments, and adds no OpenWebUI integration, deployment config, Docker config, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority.
- v0.26.0 M22 Local Model Runtime Activation Contract is contract/planning/validation only, keeps OpenAPI path count unchanged at 74, and no model was called, no runtime was activated, and no endpoint was contacted. It adds no backend route, runtime execution, local LLM call, model/provider call, endpoint probe, user prompt processing, tool execution, memory write, file write, OpenWebUI runtime behavior, dependency, or production authority.
- v0.26.1 M22 Safety Hardening tightens verifier fragments, validates metadata keys as well as values in activation policy/request/decision contracts, removes brittle local route-count unit-test ownership, and cleans duplicate M22 docs wording. It keeps OpenAPI path count unchanged at 74 and adds no backend route, runtime execution, local LLM call, model/provider call, endpoint probe, user prompt processing, tool execution, memory write, file write, OpenWebUI runtime behavior, dependency, or production authority.
- v0.27.0 M23 First Real Local LLM Call is manual/CLI-only, loopback-only, fixed-prompt-only, dry-run by default, explicitly execution-flagged, local-approval-gated, non-tool, and non-authoritative. It keeps OpenAPI path count unchanged at 74 and adds no backend route, runtime activation, endpoint probe, arbitrary prompt input, user-content model call, provider SDK, runtime package, OpenWebUI runtime bridge, Control Center execution control, tool execution, memory write, file write, dependency, or production authority. M24-M40 remain planned/provisional.
- v0.27.1 M23 Local LLM Call Safety Hardening tightens endpoint-label safety, secret-like endpoint/query rejection, forged approval resistance, response redaction/caps, CLI guardrails, policy docs, static verifier coverage, Foundation Gate criteria, and Foundation Gate report atomic write/replace safety. It keeps OpenAPI path count unchanged at 74 and adds no backend route, runtime activation, endpoint probe, arbitrary prompt input, user-content model call, provider SDK, runtime package, OpenWebUI runtime bridge, Control Center execution control, tool execution, memory write, file write, dependency, runtime behavior expansion, M24 work, or production authority. The Foundation Gate report-write fix is tooling/test hardening only and was not a v0.27.0 release blocker.
- v0.28.0 M24 Memory Provider Abstraction + Local Memory Store is governed, reviewed-write-only, local/dev-only, redacted-summary-only, source-linked, recall-oriented, and non-authoritative. It keeps OpenAPI path count unchanged at 74 and adds no backend route, automatic memory write, model-output write, local LLM output write, OpenWebUI memory write, Control Center memory mutation, mobile capture write, tool output write, raw session history store, vector DB, embeddings, cloud memory provider, context injection, dependency, production persistence, M25 claim verification, or production authority.
- v0.28.1 M24 Contract Repair + Memory Safety Hardening fixes package-root memory write request exports, hardens guard-field tests, clarifies required `source_refs`, and returns defensive copies from the in-memory local store. It keeps OpenAPI path count unchanged at 74 and adds no backend route, automatic memory write, model-output write, local LLM output write, OpenWebUI memory write, Control Center memory mutation, mobile capture write, tool output write, raw session history store, vector DB, embeddings, cloud memory provider, context injection, dependency, production persistence, M25 claim verification, or production authority.
- v0.28.2 M24 Roadmap Row Cleanup removes the duplicate/conflicting planned/provisional v0.28.1 row from the Post-M20 capability roadmap only. It keeps OpenAPI path count unchanged at 74 and adds no backend route, code behavior change, test change, dependency, M25 work, or production authority.
- future post-M20 milestone prompts check `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.
- future post-M20 milestone prompts check `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.
- future post-M20 milestone prompts check `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.
- parked work is not presented as accepted baseline.
- parked branches and tags are not merged or reactivated automatically.
- blocked capabilities remain blocked until their security lifecycle and gate criteria exist.

## Foundation Gate Doc-Check Requirements

- documentation integrity verifier passes.
- Foundation Gate includes documentation integrity when active docs are synchronized.
- `verify_all.py` calls the documentation integrity verifier.
- Codex plugin governance docs are present when active tooling policy references them.
- Developer environment docs prefer `make doctor`, `make test`, `make verify`, and `make frontend-check`.
- Developer environment docs say to use `.venv/bin/python`, not bare `python`, because shell aliases are not reliable for Codex/non-interactive shells and no global Python alias is required.
## M19 Documentation Integrity Checks

- active baseline points to v0.28.2.
- M19 is implemented as Mobile Companion Contract/API Planning only.
- M20 is implemented/released as Device Capability Broker Contract only.
- v0.23.0 / M19 is marked implemented/released in active roadmap docs.
- v0.23.1 is documented as M19 cleanup/hardening only.
- mobile docs must say no mobile app, no Android app, no iOS app, no native
  build workflow, no OS permission integration, and no mobile sensor access.
- mobile docs must say Device Capability Broker is required before sensors.
- mobile docs must say capture cannot silently become memory.
- mobile docs must say phone/mobile is not the agent brain and phone output is
  not trusted control input.
- mobile docs must say contacts/calendar remain planned/disabled.
- mobile docs must say metadata refs must not contain secrets.
- mobile docs must say external sends are not allowed.
- mobile docs must say background services are not enabled.

## M20 Documentation Integrity Checks

- active baseline points to v0.28.2.
- M20 is implemented/released as Device Capability Broker Contract only.
- M20 is contract-only.
- M20 docs say no sensors are implemented.
- M20 docs say no OS permissions are implemented.
- M20 docs say no native app is implemented.
- M20 docs say capture cannot silently become memory.
- M20 docs say Device Capability Broker output is not trusted control input by default.
- M21 is implemented/released as OpenWebUI Bridge + Chat Shell Integration Contract only.
- M22 is implemented/released contract-only by v0.26.0 and hardened by v0.26.1. M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only and hardened by v0.27.1. M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2. M25-M40 remain planned/provisional.

## M21 Documentation Integrity Checks

- active baseline points to v0.28.2.
- M21 is contract/planning/validation only.
- OpenWebUI is the preferred conversational web shell.
- OpenWebUI is not the agent brain.
- Python Agent Core remains authority.
- OpenWebUI refs are identifiers only and never authority.
- no OpenWebUI integration, deployment config, Docker config, plugin/function/pipeline/tool/admin/auth/cookie/API key/admin token workflow, browser profile access, or live OpenWebUI connection is implemented.
- no backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority is added.
- M22 is implemented/released contract-only by v0.26.0 and hardened by v0.26.1. M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only and hardened by v0.27.1. M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2. M25 remains planned/provisional.
