# Documentation Integrity Checklist

Status: Active maintenance checklist, v0.21.2

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

- docs do not claim live model/provider/network/runtime execution unless implemented and gated.
- docs do not claim mobile app, sensor access, OS permission integration, or background service exists unless implemented and gated.
- docs do not claim remote execution, tailnet/private mesh execution, or remote approvals exist unless implemented and gated.
- docs do not claim scanners, Skill Factory, self-improvement, production persistence, or external actions exist unless implemented and gated.
- docs do not claim Codex plugins, plugin installers, native build tools, Xcode workflows, simulators, Chrome authenticated profile control, Computer Use automation, cloud jobs/uploads/training, or deployment workflows are enabled unless explicitly implemented and gated.
- docs do not claim runtime readiness reports, capability matrix entries, or manual smoke reports prove production readiness or authorize execution.
- docs do not claim Control Center production authority, plugin enablement, runtime execution, remote dispatch, model/provider invocation, mobile sensor access, native build control, or production Control Center exists unless implemented and gated.
- docs do not claim design tools, design SaaS sync, UI generators, screenshot-to-code, design-to-code, or automatic design commits are enabled unless implemented and gated.
- docs do not claim OpenWebUI integration, deployment config, plugin/function/tool bridge, native CCC implementation, Android app, iOS app, macOS app, OS permission integration, signing, keystore, App Store workflow, or Play Store workflow exists unless implemented and gated.
- docs do not claim M21-M40 capabilities are implemented unless a dedicated future milestone implements and gates them.

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

- active baseline points to v0.23.0.
- M19 is implemented as Mobile Companion Contract/API Planning only.
- M20 remains planned/provisional.
- mobile docs must say no mobile app, no Android app, no iOS app, no native
  build workflow, no OS permission integration, and no mobile sensor access.
- mobile docs must say Device Capability Broker is required before sensors.
- mobile docs must say capture cannot silently become memory.
- mobile docs must say phone/mobile is not the agent brain and phone output is
  not trusted control input.
