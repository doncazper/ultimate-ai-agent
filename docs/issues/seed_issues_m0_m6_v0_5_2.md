# Seed Issues M0–M6 v0.5.2

## M0 — Repo and Stack Skeleton

- [ ] M0-001 Import v0.5.2 canonical bundle
- [ ] M0-002 Create Python Agent Core package skeleton
- [ ] M0-003 Add schema validation script
- [ ] M0-004 Add prompt registry validation script
- [ ] M0-005 Add basic FastAPI health/API boundary placeholder
- [ ] M0-006 Add Docker Compose scaffold for Postgres
- [ ] M0-007 Add .env.example
- [ ] M0-008 Add OpenWebUI config folder as optional shell
- [ ] M0-009 Add API boundary bypass test skeleton
- [ ] M0-010 Add CI validation workflow

## M1 — Contracts

- [ ] M1-001 Implement Execution Contract model
- [ ] M1-002 Implement Context Pack model
- [ ] M1-003 Add validators and enums
- [ ] M1-004 Add advanced-module blocking checks

## M2 — Event Ledger

- [ ] M2-001 Implement AgentRun model
- [ ] M2-002 Implement EventLedgerEvent model
- [ ] M2-003 Implement append-only event writer
- [ ] M2-004 Implement receipt generator
- [ ] M2-005 Add redaction helper

## M3 — Consent + Tool Broker

- [ ] M3-001 Implement Consent Grant model
- [ ] M3-002 Implement Tool Manifest model
- [ ] M3-003 Implement Tool Broker policy checks
- [ ] M3-004 Add approval-required paths

## M4 — Memory + File

- [ ] M4-001 Implement Memory Record model
- [ ] M4-002 Implement Memory Write Request model
- [ ] M4-003 Implement File Operation model
- [ ] M4-004 Implement patch proposal model

## M5 — Minimal Vertical Slice

- [ ] M5-001 Orchestrator creates contract from request
- [ ] M5-002 Context Pack loads stub project truth
- [ ] M5-003 File Manager writes generated spec to workspace
- [ ] M5-004 Memory Curator writes source-linked record
- [ ] M5-005 Event Ledger produces receipt

## M6 — Foundation Gate

- [ ] M6-001 Run contract test matrix
- [ ] M6-002 Run API boundary eval
- [ ] M6-003 Run OpenWebUI bypass eval
- [ ] M6-004 Run shadow replay harness
- [ ] M6-005 Decide gate status
