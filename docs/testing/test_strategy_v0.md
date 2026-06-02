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
M26 is Tool Execution Sandbox Contract.
M27 mentions MCP / Agent Skills / AGENTS.md.
M31 mentions iOS / Android / macOS.
M35 mentions Device Capability Broker Implementation, No Sensors.
M38 is Browser Automation Contract, No Execution.
M39 is Observability Export Adapters.
M40 is Agent Evaluation + Regression Harness.
M21-M40 remain planned/provisional.
Docs do not claim M21-M40 implementation.
Foundation Gate includes post_m20_roadmap_projection_present.
Backend OpenAPI path count remains unchanged at 74.

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
