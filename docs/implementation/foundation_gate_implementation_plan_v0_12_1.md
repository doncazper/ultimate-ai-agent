# Foundation Gate Implementation Plan v0.12.1

Status: Implemented for the M8 API validation redaction hardening patch.

## Scope

v0.12.1 adds a targeted release-blocker fix for M8 API validation responses. It keeps the simulated-only model runtime boundary from v0.12.0 and ensures invalid API payloads do not echo raw invalid input values or secret-like fields.

## Implemented

```text
src/ultimate_ai_agent/api/app.py
src/ultimate_ai_agent/core/ledger/validation.py
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/evaluators.py
tests/test_api.py
tests/test_event_redaction.py
tests/test_model_runtime_api_routes.py
tests/test_m8_gate_integration.py
```

## Validation

The Foundation Gate checks M1-M7.5 file presence and security invariants plus M8 file presence, simulated/stub runtime kinds, no real runtime calls, safe simulation endpoint, simulated-only responses, non-authoritative model output, secret prompt blocking, and sanitized M8 API validation errors.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

v0.12.1 does not implement real model/provider calls, tokenizers, billing APIs, network calls, scanner modules, browser automation, production persistence, runtime credential resolution, SDK/A2A runtime delegation, Skill Factory, self-improvement, or high-autonomy execution.
