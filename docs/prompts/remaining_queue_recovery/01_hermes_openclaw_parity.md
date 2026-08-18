# Hermes And OpenClaw Parity Recovery Contract

Status: triage-ready recovery source. This replaces no historical audit record
and grants no runtime authority.

## Outcome

Produce an evidence-gated UAA versus Hermes Agent and OpenClaw comparison,
classify real gaps, and implement only separately accepted UAA-native parity
slices. Preserve clean-room boundaries and distinguish implemented, partial,
planned, blocked, and intentionally excluded behavior.

## In Scope

- Current-source capability inventory and reproducible comparison evidence.
- UAA-native gap proposals with exact owners, dependencies, and verifiers.
- Focused fixes that remain inside an explicitly reviewed child scope.

## Out Of Scope

- Importing competitor code or private behavior.
- Provider calls, live web access, unrestricted shell, remote execution, or
  production-authority promotion.

## Acceptance

- Every comparison claim cites current repository evidence.
- Every gap is classified as close, defer, or intentionally exclude.
- Any implementation is isolated, tested, independently reviewed, and merged
  before this recovery task is complete.
