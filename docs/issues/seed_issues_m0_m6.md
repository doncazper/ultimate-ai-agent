# Seed Issues M0-M6 v0.5.1

## M0 — Repository and Canonical Foundation

- [ ] M0-001 Initialize repo and import v0.5.1 docs/schemas/prompts
- [ ] M0-002 Add schema validation script
- [ ] M0-003 Add prompt registry validation script
- [ ] M0-004 Add CI skeleton
- [ ] M0-005 Add .env.example and local dev README
- [ ] M0-006 Add ADR index and active version pointer

## M1 — Kernel Contracts

- [ ] M1-001 Implement ExecutionContract model
- [ ] M1-002 Implement ContextPack model
- [ ] M1-003 Implement contract validator
- [ ] M1-004 Implement context pack validator
- [ ] M1-005 Implement advanced-module blocking checks
- [ ] M1-006 Add unit tests for contract/context schemas

## M2 — Event Ledger

- [ ] M2-001 Implement AgentRun model
- [ ] M2-002 Implement EventLedgerEvent model
- [ ] M2-003 Implement append-only event writer
- [ ] M2-004 Implement receipt generator
- [ ] M2-005 Implement redaction rules
- [ ] M2-006 Implement replay harness v1

## M3 — Consent Ledger + Tool Broker

- [ ] M3-001 Implement ConsentGrant model
- [ ] M3-002 Implement permission check engine
- [ ] M3-003 Implement ToolManifest model
- [ ] M3-004 Implement ToolCallRequest/Result models
- [ ] M3-005 Implement mock tool broker
- [ ] M3-006 Add approval gate tests

## M4 — Memory Service + File Manager

- [ ] M4-001 Implement MemoryRecord model
- [ ] M4-002 Implement memory write/read stubs
- [ ] M4-003 Implement FileManifest model
- [ ] M4-004 Implement FileOperation model
- [ ] M4-005 Implement local file patch proposal flow
- [ ] M4-006 Add canonical precedence tests

## M5 — Orchestrator Minimal Vertical Slice

- [ ] M5-001 Implement Commander run loop stub
- [ ] M5-002 Implement prompt loading by registry
- [ ] M5-003 Generate Memory V1 spec from contract/context
- [ ] M5-004 Log run events and receipt
- [ ] M5-005 Run QA checklist

## M6 — Contract Tests and Foundation Gate

- [ ] M6-001 Implement foundation gate eval runner
- [ ] M6-002 Implement shadow replay test
- [ ] M6-003 Verify advanced modules remain blocked
- [ ] M6-004 Produce Foundation Gate review packet
