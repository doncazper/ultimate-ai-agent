# API Boundary Eval v0.5.2

## Purpose

Verify that all clients enter through the Agent Gateway/API Boundary and cannot bypass core policy systems.

## Cases

1. OpenWebUI request creates or references a valid Execution Contract.
2. TypeScript Control Center request cannot mutate memory directly.
3. Tool execution request without Tool Broker is rejected.
4. Mutating request creates Event Ledger entry.
5. Sensitive request invokes Consent Ledger and privacy-aware Model Router.
6. Receipt can be generated for a UI-triggered run.

## Pass criteria

All bypass attempts are rejected and all valid calls are logged with receipts.
