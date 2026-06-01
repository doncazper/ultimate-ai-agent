# Foundation Gate Implementation Plan v0.12.2

Status: Implemented for M8.5 Approval Authority + Runtime Authorization Bridge.

## Scope

v0.12.2 adds a local/dev approval authority boundary and proves that arbitrary approval strings are not authority. The milestone remains validation-only and non-executing.

## Implemented

```text
src/ultimate_ai_agent/core/approvals/
src/ultimate_ai_agent/core/model_router/router.py
src/ultimate_ai_agent/core/model_runtime/adapters.py
src/ultimate_ai_agent/core/tools/broker.py
src/ultimate_ai_agent/core/kernel/runner.py
src/ultimate_ai_agent/api/app.py
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/evaluators.py
scripts/verify_current_baseline.py
scripts/verify_all.py
scripts/run_foundation_gate.py
tests/test_approval_*.py
tests/test_m85_*.py
```

## Validation

The Foundation Gate checks M1-M8 invariants plus M8.5 approval authority file presence, arbitrary approval ref rejection, valid local/dev grant validation, expired/revoked grant denial, Model Router approval bridging, Model Runtime arbitrary-ref rejection, Tool Broker arbitrary-ref rejection, absence of real auth/OAuth/network/persistence code, and sanitized Approval API validation errors.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-Goals

v0.12.2 does not implement real model/provider calls, tokenizers, billing APIs, network calls, scanner modules, browser automation, production persistence, runtime credential resolution, SDK/A2A runtime delegation, production auth/OAuth, Skill Factory, self-improvement, or high-autonomy execution.
