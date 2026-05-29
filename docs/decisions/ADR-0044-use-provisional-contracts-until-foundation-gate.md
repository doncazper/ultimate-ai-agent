# ADR-0044: Use Provisional Contracts Until Foundation Gate

Status: Accepted.
Date: 2026-05-29.

## Context

Freezing Execution Contract, Context Pack, and Event Ledger schemas before real consumers risks ossifying poor abstractions.

## Decision

M1 contracts are `v0/provisional`. One controlled breaking revision is allowed after the Minimum Lovable Kernel and before Foundation Gate. Post-gate contracts are compatibility-protected.

## Consequences

Contract tests still exist immediately, but compatibility guarantees strengthen only after the first real slice proves the abstractions.

