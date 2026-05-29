# 44 — Contract Versioning and Provisional Policy

Status: Foundation contract policy, v0.5.3
Owner: Architecture / Runtime

## Purpose

Avoid freezing wrong abstractions before real consumers exist.

## Policy

M1 contracts are `v0/provisional` until the Foundation Gate passes.

This applies to:

```text
Execution Contract
Context Pack
Event Ledger Event
Agent Run
Tool Call Request/Result
Consent Grant
Memory Record
File Operation
Provider Envelope
Model Route
```

## Allowed provisional changes

Before Foundation Gate:

```text
One planned breaking revision after the Minimum Lovable Kernel.
Schema fields may be renamed if contract tests and docs update together.
Required fields may change if no production consumer exists.
```

After Foundation Gate:

```text
Breaking changes require ADR.
Migration path required.
Contract tests required.
Shadow replay required.
Compatibility window required where practical.
```

## Version markers

Schemas should include:

```text
schema_version
contract_status: provisional | active | deprecated | retired
introduced_in
superseded_by
```

## Foundation rule

Do not enforce strict backward compatibility on M1 contracts until at least two real consumers or the Foundation Gate acceptance run exists.
