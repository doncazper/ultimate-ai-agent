# Foundation Gate Implementation Plan v0.12.0

Status: Implemented for the M8 simulated model runtime adapter harness.

## Scope

v0.12.0 adds a simulated-only model runtime boundary. It validates manifests, requests, and responses; converts selected route decisions into runtime requests; and emits deterministic simulated responses without calling any real runtime.

## Implemented

```text
src/ultimate_ai_agent/core/model_runtime/__init__.py
src/ultimate_ai_agent/core/model_runtime/enums.py
src/ultimate_ai_agent/core/model_runtime/manifests.py
src/ultimate_ai_agent/core/model_runtime/requests.py
src/ultimate_ai_agent/core/model_runtime/responses.py
src/ultimate_ai_agent/core/model_runtime/simulator.py
src/ultimate_ai_agent/core/model_runtime/adapters.py
src/ultimate_ai_agent/core/model_runtime/validation.py
src/ultimate_ai_agent/core/model_runtime/redaction.py
src/ultimate_ai_agent/api/app.py
```

## Validation

The Foundation Gate checks M1-M7.5 file presence and security invariants plus M8 file presence, simulated/stub runtime kinds, no real runtime calls, safe simulation endpoint, simulated-only responses, non-authoritative model output, and secret prompt blocking.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

v0.12.0 does not implement real model/provider calls, tokenizers, billing APIs, network calls, scanner modules, browser automation, production persistence, runtime credential resolution, SDK/A2A runtime delegation, Skill Factory, self-improvement, or high-autonomy execution.
