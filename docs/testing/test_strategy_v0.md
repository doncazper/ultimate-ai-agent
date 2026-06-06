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
v0.37.4 supersedes the old active post-M33 roadmap projection. M35 is Safe
File Review Workflow Contracts, and Device Capability Broker implementation is
not the active M35 sequence.
M38 is Safe Context Proposal From Approved Review.
M39 is CCC Context Proposal Surface.
M40 is Context Handoff Approval, No Injection.
The v0.18.4 M21-M40 projection is superseded by the v0.37.4 M34-M60 roadmap;
by v0.30.0,
M26 is implemented/released as a contract-only grounded recall/context-pack foundation,
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1 for state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool and hardened by v0.36.1, M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety, v0.37.2 adds local developer launcher tooling only, v0.37.4 supersedes the active post-M33 projection, M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only, M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence, and M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review. M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40-M60 remain planned/provisional.
Docs do not claim future milestone implementation before dedicated milestones.
Foundation Gate includes post_m20_roadmap_projection_present.
Backend OpenAPI path count remains unchanged at 74.
v0.38.1 adds M34 boundary-clarity regression coverage: documentation integrity,
static verification, and Foundation Gate checks reject active docs that still
list v0.38.0 / M34 as planned/provisional or say M34 remains
planned/provisional after v0.38.0. They also reject any active claim that M34
implements Safe File Review Workflow Contracts, file review UI, approval
capture/persistence, context proposal, context injection, raw file access,
memory writes, export, execution, or runtime file authority.

v0.38.2 adds current-baseline regression coverage: documentation integrity
verification rejects active current-baseline labels that do not match the
version files. Stale active labels such as v0.38.0 or v0.38.1 fail once the
version files show v0.39.0. This is docs/verifier-only coverage and adds no
runtime behavior, backend route, frontend feature, dependency, M36 work, or
production authority.

v0.39.1 adds M35 exact file/path binding regression coverage: file review
approvals must match actor, review packet, preview result, redaction summary,
exact file_ref binding, and exact safe_path_ref binding. `review_packet_ref`
alone is not sufficient, file/path mismatches are denied, and `model_copy`
mutations to packet `file_ref` or `safe_path_ref` cannot receive review_allowed.
This adds no Control Center file review UI, approval capture, approval
persistence, backend routes, context proposal, context injection, memory writes,
export, execution, dependency, M36 work, or production authority.

v0.40.0 adds M36 CCC File Review Surface, Review-Only frontend coverage. Tests
verify `/files/review` renders visibly mock and non-authoritative redacted
review packets, redacted preview display, redaction summary display, exact
binding refs, review-only decision status, approval gate contract status, and
receipt plan metadata. Static verifiers assert the absence of approve, deny,
submit, save, mark-reviewed, export, download, copy-raw, file picker, browse,
upload, root selector, context proposal, context injection, memory write,
execute, run, tool, and model-call controls. M37 is implemented/released by
v0.41.0 and M38 is implemented/released by v0.42.0. M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40 remains planned/provisional.

v0.40.1 hardens M36 CCC File Review Surface, Review-Only coverage. Tests and
verifiers now require safe refs only, reject private path-shaped refs, raw
path-shaped labels, and traversal fragments, and confirm packet selection and
expansion are local read-only UI state with no mutating request. M37 remains
planned/provisional.

v0.42.0 adds M38 Safe Context Proposal From Approved Review contract coverage.
Tests verify exact approved-review binding across approval, review packet,
preview result, redaction summary, file, path, and actor refs; reject
approval_ref-alone authority and approval_test_ refs; deny raw content, full
file content, unredacted preview, unsafe sections, context injection,
OpenWebUI handoff, model calls, memory writes, export, and execution; and keep
receipt plans non-authoritative with safe refs only. Static verifiers and
Foundation Gate assert no backend context proposal/injection/handoff routes,
no Control Center context proposal surface, and M39-M60 remain
planned/provisional.
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
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1 for state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool and hardened by v0.36.1, M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety, v0.37.2 adds local developer launcher tooling only, M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only, M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence, and M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review. M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40-M60 remain planned/provisional.
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
M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool and hardened by v0.35.1 for hidden dynamic dispatch denial, hidden side-effect denial, evaluator revalidation, static verification, and Foundation Gate coverage. M32 is implemented/released by v0.36.0 and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety. v0.37.2 adds local developer launcher tooling only. M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only. M37 is implemented/released by v0.41.0, M38 is implemented/released by v0.42.0, and M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40-M60 remain planned/provisional.
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
M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety. v0.37.2 adds local developer launcher tooling only. M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only. M37 is implemented/released by v0.41.0, M38 is implemented/released by v0.42.0, and M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40-M60 remain planned/provisional.
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
M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1 for state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 and hardened by v0.36.1, M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety, v0.37.2 adds local developer launcher tooling only, M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only, M37 is implemented/released by v0.41.0, and M38 is implemented/released by v0.42.0. M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40-M60 remain planned/provisional.
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

## v0.54.0 M50 Mobile Approval Audit Hardening Tests

v0.54.0 adds focused mobile approval audit hardening tests only:

```text
Mobile approval audit reports are deterministic, review-only, and safe-ref-only.
M49 approve-review-only and deny-review-only capture records are revalidated before audit success.
Duplicate idempotency keys with mismatched record fingerprints are denied.
Status and decision mismatches are denied.
model_copy-mutated raw content, raw paths, context injection, memory write, export, execution, approval execution, sensor, and background collection flags are denied.
Secret-like metadata is denied without echoing secret values in safe messages.
Audit reports perform no memory write, export, execution, sensor access, background collection, backend route, native audit UI, dependency, OpenWebUI bridge, M51 work, or production authority.
Foundation Gate includes M50 mobile approval audit criteria and route/static safety checks.
OpenAPI path count remains unchanged at 75.
M51 remains planned/provisional as OpenWebUI Bridge Adapter Pilot.
```

## v0.55.0 M51 OpenWebUI Bridge Adapter Pilot Tests

v0.55.0 adds focused OpenWebUI bridge adapter pilot tests only:

```text
OpenWebUI bridge adapter policy, request, and result contracts exist.
Adapter output is safe-summary-only and returns safe refs plus safe metadata.
Agent Core remains authority and OpenWebUI is not the agent brain.
raw prompt exposure, raw provider payload exposure, raw content, live OpenWebUI connection,
OpenWebUI runtime calls, provider/model calls, model authority, tool execution, memory writes,
context injection, side effects, and approval_ref-as-authority are denied.
model_copy-mutated unsafe fields are revalidated at the adapter boundary.
Foundation Gate includes M51 adapter pilot, route boundary, static safety, and roadmap currentness criteria.
OpenAPI path count remains unchanged at 75.
M52 remains planned/provisional as OpenWebUI Safe Conversation Surface.
```

## v0.56.0 M52 OpenWebUI Safe Conversation Surface Tests

v0.56.0 adds focused OpenWebUI safe conversation surface tests only:

```text
OpenWebUI safe conversation surface policy, turn, and surface contracts exist.
Surface output is safe-summary-only and returns safe refs plus safe metadata.
Agent Core remains authority and OpenWebUI is not the agent brain.
raw prompt exposure, raw provider payload exposure, raw content, live OpenWebUI connection,
OpenWebUI runtime calls, provider/model calls, model authority, tool execution, memory writes,
context injection, side effects, and approval_ref-as-authority are denied.
model_copy-mutated unsafe fields are revalidated at the conversation surface boundary.
Foundation Gate includes M52 safe conversation surface, route boundary, static safety, and roadmap currentness criteria.
OpenAPI path count remains unchanged at 75.
M53 remains planned/provisional as Controlled Tool Expansion Review.
```

## v0.57.0 M53 Controlled Tool Expansion Review Tests

v0.57.0 adds focused controlled tool expansion review tests only:

```text
Controlled tool expansion policy, candidate, decision, and receipt plan contracts exist.
Safe metadata review candidates are review-ready only.
Effectful tool capability candidates require a future reviewed milestone.
Unknown tool capability candidates are denied.
execution_requested, tool_enablement_requested, backend route requests, Control Center controls, raw prompt/provider/tool payload flags, secret-like content flags, and approval_ref-as-authority are denied.
model_copy-mutated unsafe fields are revalidated at the evaluator boundary.
Receipt plans record no tool execution, no tool enablement, no side effects, no network call, no model call, no memory write, and no context injection.
Foundation Gate includes M53 controlled tool expansion review, static safety, route boundary, and roadmap currentness criteria.
OpenAPI path count remains unchanged at 75.
At the v0.57.0 M53 baseline, M54 remained planned/provisional as Safe Media Metadata Inspector.
```

## v0.58.0 M54 Safe Media Metadata Inspector Tests

v0.58.0 adds focused Safe Media Metadata Inspector tests only:

```text
Safe media metadata policy, request, decision, and receipt plan contracts exist.
Supported declared image, video, and audio metadata can be marked metadata-ready.
Unsupported media types are denied without raw media output.
raw_media_requested, full_file_read_requested, file_mutation_requested, original_overwrite_requested, ocio_transform_requested, ai_gamut_expansion_requested, model_call_requested, context_injection_requested, and secret-like metadata flags are denied.
model_copy-mutated unsafe fields are revalidated at the evaluator boundary.
Receipt plans record metadata-only results, no raw media storage, no original overwrite, and no side effects.
Foundation Gate includes M54 safe media metadata inspector, static safety, route boundary, and roadmap currentness criteria.
OpenAPI path count remains unchanged at 75.
At the v0.58.0 M54 baseline, M55 remained planned/provisional as Redacted Observability Export.
```

## v0.59.0 M55 Redacted Observability Export Tests

v0.59.0 adds focused Redacted Observability Export tests only:

```text
Redacted observability export policy, request, item, bundle, and receipt plan contracts exist.
Explicit safe event refs can build deterministic redacted export bundles.
Export bundles include safe event refs, safe trace refs, redacted summaries, redaction summaries, and safe metadata refs only.
raw_prompt_export_requested, raw_provider_payload_export_requested, raw_private_content_export_requested, secret_export_requested, external_saas_export_requested, network_export_requested, memory_write_requested, model_call_requested, and context_injection_requested are denied.
Secret-like event metadata and missing source event refs are denied.
model_copy-mutated unsafe fields are revalidated at the evaluator boundary.
Receipt plans record no raw prompt export, no raw provider payload export, no raw private content export, no secret export, no external delivery, no network delivery, no memory write, no model call, and no context injection.
Foundation Gate includes M55 redacted observability export, static safety, route boundary, and roadmap currentness criteria.
OpenAPI path count remains unchanged at 75.
M56 is implemented/released as Agent Eval Regression Harness. It adds focused
tests for deterministic eval case, suite, observation, result, report, and
receipt-plan contracts. The tests verify explicit safe observations can produce
deterministic pass/fail regression reports without model calls, provider calls,
tool execution, shell execution, browser automation, network access, memory
writes, context injection, raw prompt capture, raw provider payload capture,
backend routes, dependencies, production authority, or M57 work.

M57 is implemented/released as Runtime Sandbox Architecture Review. It adds
focused tests for deterministic architecture policy, request, decision, and
receipt-plan contracts. The tests verify declared sandbox boundary refs and
threat-model refs can produce architecture-review-only reports without sandbox
execution, subprocess execution, shell execution, process spawn, file mutation,
network access, tool execution, browser automation, plugin execution, remote
execution, model/provider calls, memory writes, context injection, backend
routes, dependencies, production authority, or M58 work.

M58 remains planned/provisional as Dry-Run Execution Audit Harness.
```
