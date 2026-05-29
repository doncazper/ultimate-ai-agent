# ADR-0042: Designate Trusted Computing Base

Status: Accepted for foundation v0.5.3

## Context

The plan says self-improvement cannot modify safety policies without review, but safety policy was not enumerated.

## Decision

Designate the Trusted Computing Base in `docs/canonical/45_trusted_computing_base.md`. Autonomous self-improvement may propose TCB changes but cannot apply, merge, deploy, or activate them.

## Consequences

- Safety-critical files and runtime modules receive stricter review.
- Self-improvement has a concrete boundary.
- CI and Event Ledger should later enforce TCB change detection.
