# Test Strategy v0

Status: Active for M0 through Foundation Gate.

## Purpose

Keep tests consistent across human, Codex, Hermes, and future agent-authored code. The project should use explicit test categories and names so agents do not invent incompatible testing conventions.

## Test categories

```text
unit
contract
integration
golden
security
redaction
replay
smoke
eval
foundation_gate
```

## Naming conventions

```text
test_unit_*.py
test_contract_*.py
test_integration_*.py
test_security_*.py
test_redaction_*.py
test_replay_*.py
test_foundation_gate_*.py
```

## M0 required tests

```text
JSON files parse.
JSON Schema files validate.
Prompt registry paths exist.
Core import/readme files exist.
No tracked .DS_Store files.
No obvious secret assignments committed.
FastAPI health endpoint imports and responds.
Version endpoint returns active version.
Foundation-first blocked module list is present.
```

## M1 required tests

```text
Execution Contract validates.
Context Pack validates.
ResultEnvelope validates.
ErrorEnvelope validates.
ActorContext validates.
TemporalContext validates.
Data classification propagates.
Mutable operations require idempotency metadata.
Advanced modules remain blocked by capability flags.
```

## Rule

Every bug fixed after M0 should produce either a regression test, an eval, or an explicit written reason why a test is not practical.

## M12 Control Center Contract Tests

M12 adds backend Control Center contract tests only:

```text
Control Center manifest surfaces are deterministic and read-only/preview-only.
Dashboard snapshots contain safe summaries only.
Action preview allows safe view previews and blocks execution, mutation, credential, remote, plugin, runtime, provider, and mobile sensor claims.
API routes return ResultEnvelope data and expose no execute route.
Foundation Gate includes M12 no-execution criteria.
No frontend package files, native build workflow, Browser/Chrome/Computer Use bridge, plugin enablement, model/provider calls, network calls, remote dispatch, or mobile sensor access is added.
```

## M13 Web Control Center Shell Tests

M13 adds frontend shell tests plus Python gate integration tests:

```text
React/Vite dashboard renders safe status, runtime, gate, API, approval, remote, mobile, and plugin summaries.
Mock fallback data is visibly mock and non-authoritative.
Action preview form posts only to /control-center/actions/preview.
No action-run, plugin-enable, sensor, model-run, credential-use, or remote-dispatch button exists.
Secret-like input is redacted from user-visible output.
Frontend source and package dependencies remain local shell only.
Foundation Gate includes M13 frontend safety criteria.
```

## v0.17.2 Web Control Center Verification Tests

v0.17.2 adds hardening tests for CI/static/browser-readiness safety:

```text
Frontend CI runs npm ci, typecheck, lint, tests, and build inside apps/control-center.
Browser smoke readiness documentation is manual, local-only, unauthenticated-profile-free, and non-authoritative.
Browser smoke readiness verification is static-only and does not open browsers or start servers.
Frontend safety verifier rejects forbidden endpoints, dangerous controls, sensitive browser APIs, analytics/SaaS SDK markers, secret-like fixtures, and tracked generated artifacts.
Foundation Gate includes frontend CI and browser smoke readiness criteria.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.18.4 Post-M20 Roadmap Projection Tests

v0.18.4 adds docs/verifier/gate tests only:

```text
Post-M20 roadmap projection docs exist.
M21 through M40 are mentioned.
M21 is OpenWebUI Bridge + Chat Shell Integration Contract.
M22 is Local Model Runtime Activation Contract.
M23 is First Real Local LLM Call.
M24 is Memory Provider Abstraction.
M26 is Grounded Recall Router + Evidence-Linked Context Pack Builder.
M27 is Tool Broker v2 + Safe Tool Intent Contracts.
M31 mentions Real Tool Runtime Adapter, Single Safe No-Op Tool.
M35 mentions Device Capability Broker Implementation, No Sensors.
M38 is Browser Automation Contract, No Execution.
M39 is Observability Export Adapters.
M40 is Agent Evaluation + Regression Harness.
M21-M40 remain planned/provisional in the v0.18.4 projection; by v0.30.0,
M26 is implemented/released as a contract-only grounded recall/context-pack foundation,
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1 for state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, and M32-M40 remain planned/provisional.
Docs do not claim future milestone implementation before dedicated milestones.
Foundation Gate includes post_m20_roadmap_projection_present.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.29.0 M25 Truth Source Router + Evidence Claim Checker Tests

v0.29.0 adds contract, verifier, and Foundation Gate tests only for M25:

```text
Truth source refs validate structured refs and safe metadata.
Source priority ranks canonical/evidence/receipt/Event Ledger/user-reviewed sources above memory.
Claims and evidence chains reject raw prompts, raw files, raw memory, raw credentials, and raw provider payloads.
Claim decisions require primary/source-backed evidence for verified status.
Memory-only and model-output-only evidence cannot verify truth.
Conflicted, stale, revoked, or missing evidence produces safe review/deny decisions.
External verification, web search, source fetching, model/provider calls, retrieval/RAG, vector DB, embeddings, memory writes, and evidence mutation remain blocked.
M25 adds no backend API route and OpenAPI path count remains unchanged at 74.
M26 is implemented/released by v0.30.0 as Grounded Recall Router + Evidence-Linked Context Pack Builder.
```

## v0.29.3 Documentation Archive Structure Tests

v0.29.3 adds documentation-integrity tests and verifier checks only:

```text
docs/README.md and docs archive entrypoints exist.
Current release packets live under docs/archive/releases/v0_29_3/.
Root historical release packets are no longer active start files.
Historical roadmap snapshots are marked historical or archived.
Active docs identify v0.29.3 as docs organization only.
M25 remains implemented/hardened.
At v0.29.3 release time, M26 remained planned/provisional.
OpenAPI path count remains unchanged at 74.
```

## v0.29.4 Documentation Archive Reference Repair Tests

v0.29.4 adds documentation-integrity tests and verifier checks only:

```text
Historical version verifiers do not live at root or under active scripts/.
Archived historical verifiers are marked historical and not part of current validation.
Current release packets live under docs/archive/releases/v0_29_4/.
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md is indexed.
Stale Ruff excludes for retired historical verifier paths are absent.
Active docs identify v0.29.4 as documentation archive reference repair only.
```

## v0.30.0 M26 Grounded Recall Router + Evidence-Linked Context Pack Builder Tests

v0.30.0 adds contract, verifier, and Foundation Gate tests only for M26:

```text
Grounded Recall Router selects from provided candidates only.
Source priority ranks canonical/evidence/receipt/Event Ledger/user-reviewed refs above memory.
Memory may provide recall context only and cannot become truth authority.
Unknown, arbitrary, stale, conflicted, revoked, deleted, superseded, model-output, runtime-output, and OpenWebUI-output candidates are excluded.
Evidence-linked context packs contain refs, safe summaries, provenance, and redaction status only.
Raw prompts, raw model output, raw files, raw memory, raw transcripts, credentials, and secret-like metadata are rejected.
Context-pack building does not inject context into a model, runtime, OpenWebUI, tool, or agent loop.
Vector search, embeddings, semantic search, RAG ingestion, external retrieval, web search, source crawling, model/provider calls, memory writes, evidence mutation, and Event Ledger mutation remain blocked.
M26 adds no backend API route and OpenAPI path count remains unchanged at 74.
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization.
OpenAPI path count remains unchanged at 74.
```

## v0.30.1 M26 Recall Source Identity Hardening Tests

v0.30.1 adds focused regression, verifier, and Foundation Gate tests only for
M26 hardening:

```text
source_ref/source_kind consistency is enforced before recall selection.
memory refs cannot be upgraded to canonical/evidence/receipt/event/user-reviewed priority by caller-declared source_kind.
model, runtime, and OpenWebUI refs are denied regardless of declared source_kind.
unknown prefixes remain denied.
context packs reject mismatched selected items.
Foundation Gate and verify_all.py probe the same mismatch bypass.
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1 for state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, and M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
OpenAPI path count remains unchanged at 74.
```

## v0.32.0 M28 Approval Authority v2 + Action Policy Expansion Tests

v0.32.0 adds contract, verifier, and Foundation Gate tests only for M28:

```text
Approval Authority v2 manifest disables action execution, tool execution, file mutation, memory writes, network actions, browser/mobile/remote/plugin/model actions, wildcard approvals, approval_test refs, backend execution routes, and production authority.
Action Policy can allow safe no-effect/read-metadata policy decisions only with execution_authorized=False and execution_performed=False.
approval_ref alone is denied.
approval_test_ refs are denied as runtime authority.
consent_ref alone is denied.
wildcard approval scope is denied.
expired, revoked, replayed, and actor/action/resource/scope-mismatched grants are denied.
model, memory, context-pack, and tool-intent refs cannot authorize action policy decisions.
raw prompt/model/file/transcript content and secret-like metadata are rejected.
receipt plans are non-authoritative and store no raw content.
Foundation Gate and verify_all.py probe the same approval/action-policy boundary.
M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
OpenAPI path count remains unchanged at 74.
```

## v0.32.1 M28 Evaluator Revalidation Tests

v0.32.1 adds focused regression, verifier, and Foundation Gate tests only for
M28 hardening:

```text
ActionPolicy evaluator revalidates ActionIntent, ApprovalGrant, and ActionPolicy objects before allowing policy-only decisions.
ActionIntent.model_copy(update=...) cannot smuggle raw prompt/model/file/transcript flags into an allowed decision.
ActionIntent.model_copy(update=...) cannot smuggle secret-like summaries, metadata, or metadata refs into an allowed decision.
ApprovalGrant.model_copy(update=...) cannot smuggle approval_test_ grant refs, secret metadata, expired/revoked state, replayed nonces, wildcard scope, or mismatched actor/action/resource/scope bindings into an allowed decision.
Safe no-effect/read-metadata decisions remain policy-only with execution_authorized=False and execution_performed=False.
Foundation Gate and verify_all.py probe the same mutated-object revalidation boundary.
M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
OpenAPI path count remains unchanged at 74.
```

## v0.29.1 M25 Reject Unknown Truth Refs Tests

v0.29.1 adds focused regression, verifier, and Foundation Gate tests only for
M25 hardening:

```text
Inferred unknown refs such as random:source cannot produce evidence_supported.
Explicit TruthSourceKind.unknown evidence cannot produce evidence_supported.
Unknown refs cannot produce verified_by_primary_source.
Unknown refs cannot produce allowed source_linked status.
Claim self-verification remains denied.
Valid recognized canonical primary-source evidence still succeeds.
M25 adds no backend API route and OpenAPI path count remains unchanged at 74.
M26 is implemented/released by v0.30.0; M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts; v0.31.1 is docs-only README polish baseline normalization.
```

## v0.29.2 M25 Local Dev API Authority And Raw Preview Tests

v0.29.2 adds focused regression, verifier, and Foundation Gate tests only for
M25 hardening:

```text
Tool Broker no longer treats approval_test_* refs as fallback authority.
MinimumKernelRunner rejects test-prefixed approval refs without explicit LocalApprovalAuthority.
Public /kernel/tasks/run local-dev mutation requests are dry-run-only and do not write files.
Public file read preview responses are metadata-only by default and mark raw_content_omitted.
Secret-like file preview refs are rejected without echoing hostile paths or values.
API handlers do not use raw exception strings as safe messages or details.
Direct truth memory/model authority helpers fail closed for unsafe refs.
M25 adds no backend API route and OpenAPI path count remains unchanged at 74.
At v0.29.2 release time, M26 remained future as Grounded Recall Router + Evidence-Linked Context Pack Builder.
```

## v0.19.0 M15 Approval Receipt Event Viewer Tests

v0.19.0 adds frontend, verifier, and Foundation Gate tests only for M15 UI:

- Approval Queue route renders read-only/preview-only summaries and selected details.
- Receipt Viewer route renders redacted summary-only receipt summaries and selected details.
- Event Viewer route renders redacted event summaries and selected details.
- M15 mock data is visibly mock and non-authoritative.
- active approval/action controls and mutation endpoints are absent.
- static frontend verifier rejects approval execution, approve/reject mutation, receipt mutation, raw event, raw memory, raw file, sensitive browser storage, credential field, unsafe dependency, generated artifact, and unsafe API base drift.
- Foundation Gate criterion `m15_approval_receipt_event_ui_safe` exists and passes.

Backend OpenAPI path count remains unchanged at 74.
```

## v0.19.1 M15 Approval Receipt UI Safety Hardening Tests

v0.19.1 adds focused frontend, verifier, and Foundation Gate hardening tests only:

```text
Approval Queue route states that the UI cannot grant, deny, execute, or bypass approvals.
Approval refs are identifiers only and never authority.
Python Agent Core remains the only approval authority.
Receipt detail views state that they are redacted summary metadata only.
Event detail views state that they are redacted summary metadata only.
Static frontend verifier rejects raw M15 review fields and credential-like review fields.
Static frontend verifier requires approval authority-boundary copy.
Foundation Gate rejects authority-bypass copy and raw sensitive fields.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.20.0 M16 Event Timeline Trace Viewer Tests

v0.20.0 adds focused frontend, verifier, and Foundation Gate tests only:

```text
Event Timeline route renders read-only redacted timeline summaries.
Run/receipt trace panel renders selected summary metadata only.
Event relation/ref panel renders parent/child and receipt/evidence relationship summaries.
Foundation Gate evidence summary panel renders safe evidence refs and statuses.
Static frontend verifier rejects raw M16 trace fields and credential-like trace fields.
Static frontend verifier rejects trace raw/export endpoints and dangerous controls.
Static frontend verifier requires M16 read-only, summary-only, no-export boundary copy.
Foundation Gate criterion m16_event_timeline_trace_viewer_safe exists and passes.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.20.1 M16 Trace Redaction Safety Hardening Tests

v0.20.1 adds focused hardening tests only:

```text
Event Timeline interaction test clicks a second View trace control.
Selected trace detail changes to the second safe event ref.
Selected timeline card exposes an accessible selected-state marker.
Trace selection remains read-only and mock/non-authoritative.
No execute, run, export, send, write, deploy, or enable controls appear.
No raw prompt, secret, file, memory, credential, provider payload, or raw event content appears.
Foundation Gate checks OpenAPI path count remains 74.
Foundation Gate rejects backend timeline, trace, raw event, and telemetry export route expansion.
Static frontend verifier rejects tracked Control Center build and log artifacts.
Review builds prefer temporary Vite output paths such as `npm run build -- --outDir /tmp/uaa-control-center-review-dist`.
Generated frontend artifacts remain ignored and untracked.
```

## v0.21.0 M17 Evidence File Memory Viewer Tests

v0.21.0 adds focused frontend, verifier, and Foundation Gate tests only:

```text
Evidence Viewer route renders read-only redacted evidence ref summaries.
File Reference Viewer route renders safe file ref metadata without raw file contents.
Memory Viewer route renders recall-only memory ref summaries.
Memory is recall, not authority.
Canonical files and governed source systems outrank memory.
No file mutation, memory mutation, filesystem browsing, execute, run, reveal raw, or show raw controls appear.
No raw prompt, secret, file, memory, evidence, credential, provider payload, or private path appears.
Static frontend verifier rejects raw M17 knowledge fields and credential-like knowledge fields.
Static frontend verifier rejects private path fragments in M17 mock fixtures.
Static frontend verifier requires M17 read-only, summary-only boundary copy.
Foundation Gate criterion m17_evidence_file_memory_viewer_safe exists and passes.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.21.1 M17 Evidence File Memory Viewer Safety Hardening Tests

v0.21.1 adds focused frontend, verifier, and Foundation Gate hardening tests only:

```text
Alternate Evidence Viewer mock metadata can be selected and remains read-only.
Alternate File Reference Viewer mock metadata can be selected and remains read-only.
Alternate Memory Viewer mock metadata can be selected and remains recall-only.
Selected summary cards expose accessible selected-state markers.
All selected alternate metadata remains visibly mock, non-authoritative, and redacted summary-only.
No file mutation, memory mutation, filesystem browsing, execute, run, reveal raw, or show raw controls appear.
Static frontend verifier requires M17 hardening mock markers.
Static frontend verifier requires M17 selected-state markers.
Foundation Gate criterion m17_evidence_file_memory_viewer_hardening_safe exists and passes.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.21.2 Developer Environment Command Normalization Tests

v0.21.2 adds focused dev tooling tests only:

```text
Dev environment verifier checks `.venv/bin/python` exists.
Dev environment verifier prints the venv Python version.
Dev environment verifier confirms `ultimate_ai_agent`, pytest, and Ruff are importable through the venv Python.
Dev environment verifier prints remediation using `python3 -m venv .venv` and `.venv/bin/python -m pip install -e ".[dev]"`.
Control Center package metadata is detected when `apps/control-center` exists.
Missing npm is a warning unless frontend checks are explicitly required by the current repo convention.
Makefile targets `doctor`, `test`, `verify`, `frontend-check`, `openapi`, and `ruff` use `.venv/bin/python`.
Repo verification commands should use `.venv/bin/python` or Makefile targets, not bare `python`.
Shell aliases are not reliable for Codex/non-interactive shells.
No global Python alias is required.
No runtime behavior, frontend behavior, backend API route, dependency, network call, plugin enablement, or production capability is added.
```

## v0.18.3 OpenWebUI and CCC Strategy Tests

v0.18.3 adds docs/verifier/gate tests only:

```text
Required docs/ui files exist.
OpenWebUI is the preferred conversational web shell.
OpenWebUI is not the agent brain.
CCC means Control Center Clients.
CCC is the governance/control layer.
CCC Web, CCC iOS, CCC Android, and CCC macOS are defined.
Open Design does not replace OpenWebUI.
CCC native clients remain future-only.
No OpenWebUI integration, deployment config, native CCC implementation, Android app, iOS app, macOS app, native build workflow, mobile sensor access, OS permission integration, signing, keystore, App Store, or Play Store workflow is added.
Foundation Gate includes openwebui_ccc_strategy_docs_present.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.23.1 M19 Cleanup And Mobile Contract Safety Tests

v0.23.1 adds cleanup/hardening tests only:

```text
Roadmap currentness marks v0.23.0 / M19 implemented/released.
Roadmap currentness marks v0.24.0 / M20 implemented/released as contract-only.
M21-M40 were planned/provisional at M19 cleanup time. By v0.30.0, M26 is
implemented/released as a contract-only grounded recall/context-pack foundation,
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1 for state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, and M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
Contacts and calendar capability plans cannot be enabled.
Contacts and calendar capability plans require a future Device Capability Broker.
Contacts and calendar cannot be represented as implemented.
Metadata refs reject secret-like values.
External sends are rejected independently.
OS permission integration flags are rejected.
Background service flags are rejected.
No backend API route, dependency, mobile app, Android app, iOS app, macOS app,
native build workflow, mobile sensor access, OS permission integration,
background service, notification runtime, Device Capability Broker
implementation, runtime execution, model/provider call, remote execution,
plugin enablement, or production authority is added.
```

## v0.17.4 Web Control Center Local Smoke Polish Tests

v0.17.4 adds focused frontend and static documentation tests only:

```text
Every local Web Control Center page has a clear route heading for browser smoke review.
Loading and empty states expose accessible status text and read-only wording.
Action preview displays risk level as preview metadata and still posts only to /control-center/actions/preview.
Secret-like backend preview errors are redacted before user-visible display.
Local browser smoke reporting docs remain local-only, non-authoritative, and free of generated artifact requirements.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.18.0 M14 Local Backend Connection Tests

v0.18.0 adds focused frontend and static gate tests only:

```text
API base URL policy allows relative, localhost, 127.0.0.1, and loopback IPv6 bases.
External absolute API bases are blocked.
Secret-like API base URL strings are rejected and redacted.
The Web Control Center displays backend online state when all local read requests succeed.
The Web Control Center displays degraded state when some local read requests fail and non-authoritative mock fallback fills missing panels.
Mock fallback remains visibly non-authoritative when the backend is unavailable or the base URL is rejected.
Frontend safety verifier requires the local backend base policy and rejects external API URL markers.
Foundation Gate includes M14 local backend connection criteria.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.18.2 Open Design Governance Tests

v0.18.2 adds docs/verifier/gate tests only:

```text
Required docs/design files exist.
Design docs say no design tools are enabled.
Design docs say the design source of truth is repo-owned.
Design docs say screenshots and design artifacts must not contain secrets.
Control Center docs link design governance docs.
Foundation Gate includes open_design_governance_docs_present.
Backend OpenAPI path count remains unchanged at 74.
```

## v0.24.0 M20 Device Capability Broker Contract Tests

v0.24.0 adds contract-only tests for future device capabilities:

```text
default Device Capability Broker manifest is contract-only.
all device capabilities are allowed_now=false and implemented_now=false.
camera/microphone/location/notifications/contacts/calendar/photos/files/clipboard/Bluetooth/NFC/biometrics remain planned/disabled.
silent capture, background capture, passive capture, continuous capture, raw payloads, automatic memory writes, external sends, OS permission integration, background services, runtime pairing claims, and device-client authority are rejected.
docs/device_capabilities files exist.
Foundation Gate includes m20_device_capability_broker_contract_safe.
OpenAPI path count remains unchanged at 74.
M21 is implemented/released by v0.25.0 as OpenWebUI Bridge + Chat Shell Integration Contract only.
```

## v0.24.1 M20 Hardening Tests

v0.24.1 adds focused hardening tests only:

```text
every major DeviceCapabilityKind rejects allowed_now=true.
every major DeviceCapabilityKind rejects implemented_now=true.
permission contracts reject OS permission runtime, notification push runtime, and background service runtime claims.
validation decisions cannot allow device capability runtime authority.
receipt plans require redacted receipts and no raw storage.
revocation plans remain contract-only.
raw payload-like metadata, geolocation coordinates, private local paths, and secret-like text are rejected.
static frontend verifier rejects expanded device capability and mobile permission/background-service route drift.
Foundation Gate rejects expanded device capability backend routes and keeps OpenAPI path count at 74.
M21 is implemented/released by v0.25.0 as OpenWebUI Bridge + Chat Shell Integration Contract only.
No Device Capability Broker runtime implementation, mobile app, native build workflow, sensor API, OS permission code, backend API route, dependency, runtime execution, model/provider call, remote execution, plugin enablement, or architecture behavior change is added.
```

## v0.25.0 M21 OpenWebUI Bridge Contract Tests

v0.25.0 adds contract/planning/validation tests only:

```text
OpenWebUI bridge docs exist.
OpenWebUI is the preferred conversational web shell.
OpenWebUI is not the agent brain.
Python Agent Core remains authority.
chat ingress/egress contracts are summary/ref/redacted-metadata only.
raw content, secret-like metadata, arbitrary approval authority, direct tool execution, direct memory writes, runtime calls, provider calls, action execution, and approval grants are rejected.
static verifiers reject OpenWebUI runtime/config/dependency/route drift.
Foundation Gate includes m21_openwebui_bridge_contract_safe.
OpenAPI path count remains unchanged at 74.
M22 is implemented/released contract-only by v0.26.0. M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.
No OpenWebUI integration, deployment config, Docker config, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority is added.
```
