# Next Sequence v0.17.5

Status: Active roadmap projection and M14-M20 milestone charter freeze.

v0.17.5 freezes the next canonical sequence after the v0.17.x Web Control Center shell hardening work. Items after v0.17.5 are planned/provisional but canonical until superseded by a reviewed roadmap patch.

This document resolves the M14 ambiguity:

- M14 is **Web Control Center Local Backend Connection Stabilization**.
- Approval Queue + Receipt/Event Viewer UI moves to **M15**.
- Local browser smoke / UX polish was **v0.17.4**, not M14.

No item in this sequence may add production Control Center authority, runtime execution, model/provider calls, network calls, remote execution, mobile sensor access, plugin enablement, native build workflows, production persistence, or external actions unless a future reviewed milestone explicitly changes the boundary.

## 1. v0.17.5 - Roadmap Projection + M14-M20 Milestone Charter Freeze

Status: current docs-only patch.

Purpose: freeze the next milestone sequence so Codex, ChatGPT, GitHub, and the roadmap use the same source of truth.

Allowed scope:

- roadmap docs.
- canonical docs.
- release/version docs.
- conservative documentation verifier checks.
- optional Foundation Gate documentation criterion.

Must not add:

- M14 implementation.
- frontend features.
- backend API routes.
- runtime execution.
- model/provider calls.
- network calls.
- remote execution.
- mobile app code or mobile sensor APIs.
- plugin enablement.
- dependencies.
- architecture changes.

Acceptance criteria:

- milestone charter template exists.
- next sequence doc exists.
- active roadmap links both docs.
- M14/M15 ambiguity is resolved.
- v0.17.4 remains browser smoke / UX polish.
- docs and gate checks prevent future drift.

Review prompt required: yes, before any follow-on implementation.

Hardening patch expectation: not applicable; this is a roadmap freeze patch.

Source-of-truth docs:

- `docs/roadmap/MILESTONE_CHARTERS.md`
- `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`
- `docs/canonical/09_roadmap.md`

## 2. v0.18.0 / M14 - Web Control Center Local Backend Connection Stabilization

Status: planned/provisional.

Purpose: make the Web Control Center reliably connect to local backend APIs while keeping it read-only/preview-only.

Allowed scope:

- backend API health connection states.
- UI online, offline, and backend-unavailable states.
- typed API client hardening.
- retry and error boundaries.
- mock-to-live transition clarity.
- localhost-only docs.
- CORS or dev proxy docs when simple and local-only.

Must not add:

- new Control Center authority.
- runtime execution.
- new backend action routes.
- model/provider calls.
- remote/mobile/plugin execution.
- approval queue or receipt viewer UI, unless limited to existing read-only summaries and explicitly scoped.
- auth, credential handling, cookies, or sensitive browser storage.
- external URLs beyond local development endpoints.

Acceptance criteria:

- local backend connection states are explicit and safe.
- backend-unavailable state remains mock/non-authoritative when fallback data is shown.
- no frontend POST target is added beyond `/control-center/actions/preview`.
- no backend API path is added unless a reviewed M14 prompt explicitly authorizes it.
- docs explain localhost-only connection behavior.

Review prompt required: yes.

Hardening patch expectation: v0.18.1.

Source-of-truth docs:

- `docs/control_center/WEB_CONTROL_CENTER_SHELL.md`
- `docs/control_center/FRONTEND_SAFETY_POLICY.md`
- `docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md`
- `docs/control_center/CONTROL_CENTER_CONTRACT.md`

## 3. v0.18.1 - M14 Hardening: Control Center Backend Connection Safety

Status: planned/provisional.

Purpose: harden M14 connection behavior and prevent local backend connection work from becoming authority, credential handling, or external network access.

Allowed scope:

- static safety checks.
- error non-echo checks.
- localhost-only endpoint checks.
- documentation and tests for connection-state safety.

Must not add:

- external URLs.
- auth or credential handling.
- sensitive browser storage.
- backend execution routes.
- runtime/model/provider/network/remote/mobile/plugin execution.

Acceptance criteria:

- static verifiers reject unsafe connection targets and sensitive browser APIs.
- error displays do not echo raw invalid input or secret-like values.
- connection state remains non-authoritative.

Review prompt required: yes.

Hardening patch expectation: this is the hardening patch for M14.

Source-of-truth docs:

- `docs/control_center/FRONTEND_SAFETY_POLICY.md`
- `scripts/verify_control_center_frontend.py`

## 4. v0.18.2 - Open Design System + UI Design Governance

Status: implemented.

Purpose: define open design-system and UI governance before larger Control Center UI expansion.

Allowed scope:

- design-governance docs.
- visual language guidance.
- accessibility baseline docs.
- design-token roadmap docs.

Must not add:

- design tooling enablement.
- new frontend behavior.
- frontend dependencies.
- analytics/auth/payment/SaaS SDKs.
- production Control Center authority.

Acceptance criteria:

- design governance docs exist.
- future UI prompts must read design governance before implementation.
- design rules preserve read-only/preview-only Control Center safety.

Review prompt required: yes.

Hardening patch expectation: may be paired with the next UI milestone review.

Source-of-truth docs:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/DESIGN_TOOLING_POLICY.md`
- `docs/design/DESIGN_TOKEN_ROADMAP.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`

## 5. v0.19.0 / M15 - Approval Queue + Receipt/Event Viewer UI

Status: planned/provisional.

Purpose: show approval queue summaries, approval details, receipt summaries, and event summaries in the Web Control Center.

Allowed scope:

- read-only approval queue summaries.
- read-only approval detail views.
- read-only receipt and event summaries.
- preview-only action requests where already supported by backend contracts.

Must not add:

- approval execution unless a separate backend contract exists and is explicitly authorized.
- send/write/execute controls.
- hidden approval bypass.
- arbitrary approval strings as authority.
- credential resolution.
- remote dispatch.
- plugin enablement.
- mobile sensor control.

Acceptance criteria:

- UI is read-only/preview-only.
- approval authority remains in the Python Agent Core.
- receipts and events are redacted and safe.
- no dark patterns imply approval or execution authority.

Review prompt required: yes.

Hardening patch expectation: v0.19.1.

Source-of-truth docs:

- `docs/security/approval_authority.md`
- `docs/canonical/20_user_control_center.md`
- `docs/control_center/ACTION_PREVIEW_POLICY.md`

## 6. v0.19.1 - M15 Hardening: Approval/Receipt UI Safety

Status: planned/provisional.

Purpose: harden approval and receipt/event UI against authority bypass, dark patterns, and secret leakage.

Allowed scope:

- no-dark-pattern checks.
- authority-boundary tests.
- receipt/event redaction checks.
- static frontend safety checks.

Must not add:

- approval execution.
- send/write/run controls.
- credential handling.
- raw secret, prompt, file, or memory display.

Acceptance criteria:

- approval UI cannot bypass Approval Authority.
- receipt/event views redact sensitive content.
- no UI text or control implies execution authority.

Review prompt required: yes.

Hardening patch expectation: this is the hardening patch for M15.

Source-of-truth docs:

- `docs/security/approval_authority.md`
- `docs/canonical/51_redaction_and_safe_debugging.md`

## 7. v0.20.0 / M16 - Event Timeline + Run/Receipt Trace Viewer

Status: planned/provisional.

Purpose: provide read-only timeline and trace views for runs, events, receipts, and Foundation Gate evidence.

Allowed scope:

- read-only event timeline.
- run/receipt trace summaries.
- safe links to evidence refs.

Must not add:

- execution controls.
- raw secrets.
- raw prompts.
- raw file content.
- raw memory content.
- production telemetry export.

Acceptance criteria:

- trace views are read-only.
- sensitive event content is redacted.
- model output remains non-authoritative.

Review prompt required: yes.

Hardening patch expectation: focused trace/redaction hardening before M17.

Source-of-truth docs:

- `docs/canonical/22_observability_and_event_ledger.md`
- `docs/canonical/63_observability_standards_mapping.md`

## 8. v0.21.0 / M17 - Evidence/File/Memory Viewer

Status: planned/provisional.

Purpose: add governed read-only views for evidence refs, file refs, and memory records.

Allowed scope:

- evidence metadata views.
- file reference summaries.
- memory record summaries.
- safe redacted previews only when a future contract explicitly allows them.

Must not add:

- raw sensitive content without explicit contract.
- file writes.
- memory mutation.
- production persistence changes.
- broad filesystem scanning.

Acceptance criteria:

- canonical files outrank memory.
- memory remains recall, not authority.
- file and evidence views are redacted and read-only.

Review prompt required: yes.

Hardening patch expectation: focused evidence/file/memory redaction hardening.

Source-of-truth docs:

- `docs/canonical/03_memory_system.md`
- `docs/canonical/10_file_management.md`
- `docs/canonical/59_truth_grounding_and_evidence_governance.md`
- `docs/canonical/61_evidence_manifest_and_claim_verification.md`

## 9. v0.22.0 / M18 - Local Runtime Status + Manual Smoke Control Surface

Status: planned/provisional.

Purpose: show local runtime readiness and manual smoke status without turning it into general model execution.

Allowed scope:

- read-only local runtime status.
- manual smoke report summaries.
- approval-gated manual smoke readiness metadata.

Must not add:

- general model execution.
- user-content model calls.
- provider SDK calls.
- tokenizers or billing APIs.
- public smoke execute API.
- production readiness claims.

Acceptance criteria:

- manual smoke remains manual-only, approval-gated, fixed-prompt-only, loopback-only, and non-authoritative.
- local runtime status cannot execute models.

Review prompt required: yes.

Hardening patch expectation: focused runtime/smoke safety hardening.

Source-of-truth docs:

- `docs/runtime/RUNTIME_READINESS.md`
- `docs/runtime/MANUAL_SMOKE_REPORTS.md`
- `docs/runtime/RUNTIME_CAPABILITY_MATRIX.md`

## 10. v0.23.0 / M19 - Mobile Companion Contract/API Planning

Status: planned/provisional.

Purpose: extend mobile companion planning into reviewed API/contract docs without implementing a mobile app.

Allowed scope:

- mobile contract docs.
- API planning docs.
- permission and receipt flow planning.

Must not add:

- mobile app implementation.
- iOS, Android, React Native, Expo, Flutter, Swift, Kotlin, Capacitor, or Ionic code.
- mobile sensor access.
- OS permission integration.
- background services.
- autonomous mobile action.
- native build workflows.

Acceptance criteria:

- phone remains a future control, approval, capture, receipt, and status surface.
- phone is not the agent brain.
- sensor output is not trusted control input by default.

Review prompt required: yes.

Hardening patch expectation: mobile contract safety review before M20.

Source-of-truth docs:

- `docs/canonical/64_mobile_companion_and_device_capability_broker.md`
- `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`

## 11. v0.24.0 / M20 - Device Capability Broker Contract

Status: planned/provisional.

Purpose: define the Device Capability Broker contract before any mobile sensor implementation.

Allowed scope:

- contract docs.
- schema planning docs.
- permission lifecycle docs.
- risk and redaction policy docs.

Must not add:

- sensor access.
- mobile background services.
- silent memory writes.
- autonomous mobile action.
- OS permission integration.
- native app code.

Acceptance criteria:

- every future device capability declares purpose, risk, permission scope, retention, redaction, logging, receipt, and revocation behavior.
- mobile sensor capture cannot silently become memory or approve actions.

Review prompt required: yes.

Hardening patch expectation: Device Capability Broker safety review before implementation work.

Source-of-truth docs:

- `docs/canonical/64_mobile_companion_and_device_capability_broker.md`
- `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`
