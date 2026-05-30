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
