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
