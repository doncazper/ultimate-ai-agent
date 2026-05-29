# 38 — Scalable Stack and UI Strategy v0.5.2

Status: Accepted foundation architecture.

## Purpose

Define the implementation stack and UI strategy for the Ultimate AI Agent before coding begins, so the project can scale without confusing the chat interface, user control layer, and agent brain.

## Decision summary

Use a hybrid stack:

```text
Python Agent Core
  Orchestrator, contracts, context packs, model router, event ledger,
  consent ledger, tool broker, memory service, file manager, QA/evals,
  workers, code execution control, research workflows.

TypeScript Control Center
  User-facing web app, dashboards, approvals, memory review,
  permissions, scanner/watchlist configuration, cost view, receipts,
  settings, typed API clients, browser extension later.

OpenWebUI Chat Shell
  Early self-hosted chat interface and model playground.
  It is a window into the agent, not the agent brain.

Postgres
  Canonical durable database for foundation state.

Docker Compose
  Local development and reproducible startup.
```

The project should not be TypeScript-only or Python-only. It should use each language where it is strongest.

## Non-negotiable rule

> OpenWebUI may be a chat UI, but it must not own long-term memory, consent, event logs, tool permissions, canonical files, rollback, scanners, self-improvement, or model-routing policy.

All durable state and governed actions belong to the Agent Core.

## Why Python for the Agent Core

Python is the best default for the first implementation because the foundation depends heavily on:

```text
Pydantic-style schemas and validators
FastAPI service boundary
agent orchestration
AI/model provider integration
memory and retrieval workflows
file/document processing
code execution control
research workflows
evals and test harnesses
sandbox scripts
background workers
```

Python should own the first implementation of:

```text
Execution Contract
Context Pack
Model Router
Event Ledger
Consent Ledger
Tool Broker
Memory Service
File Manager
QA/Evals
Foundation Gate tests
```

## Why TypeScript for the Control Center

TypeScript is strongest for the user-facing app layer and API-heavy interfaces where typed contracts, refactoring safety, editor tooling, and frontend maintainability matter.

TypeScript should own or eventually own:

```text
User Control Center
Approvals Queue
Memory Viewer/Editor
Permission and Consent Settings
Scanner and Watchlist Settings
Notification Center
Cost Dashboard
Event Receipts / Activity Log
Skill Registry UI
Model Routing Preferences UI
Browser Extension
Typed API Client
```

The TypeScript app should call the Agent Core through a stable API boundary. It must not talk directly to the database or bypass the Tool Broker.

## OpenWebUI role

Use OpenWebUI for:

```text
early chat interface
model experimentation
local/cloud provider testing
developer-facing chat shell
quick interaction with Agent Core
```

Do not use OpenWebUI as:

```text
memory system
permission system
event ledger
file manager
tool execution authority
scanner scheduler
self-improvement runtime
source of canonical truth
```

OpenWebUI should connect to the Agent Core through one of these controlled patterns:

```text
OpenAI-compatible Agent Gateway
OpenWebUI Pipeline / proxy to Agent Core
MCP/OpenAPI bridge whose tools are still mediated by Tool Broker
```

## Architecture

```text
User
  ↓
OpenWebUI Chat Shell        TypeScript Control Center
  ↓                         ↓
Agent Gateway / Stable API Boundary
  ↓
Python Agent Core
  ├─ Commander / Orchestrator
  ├─ Execution Contract
  ├─ Context Pack
  ├─ Model Router
  ├─ Event Ledger
  ├─ Consent Ledger
  ├─ Tool Broker
  ├─ Memory Service
  ├─ File Manager
  └─ QA / Evals
  ↓
Postgres + Object Storage + Workers + Model Providers + Tools
```

## Recommended repository layout

```text
/apps
  /control-center          # TypeScript/Next.js app, added after Agent Core skeleton
  /openwebui               # Docker/config/proxy only; no durable agent brain

/services
  /agent-core              # Python FastAPI/Pydantic runtime
  /workers                 # Python background workers
  /tool-servers            # MCP/OpenAPI tool services later

/packages
  /schemas                 # JSON Schema/OpenAPI contracts
  /ts-client               # generated TypeScript client later
  /python-client           # optional generated Python client

/docs
  /canonical
  /decisions
  /definitions
  /evals
  /implementation
  /prompts
  /registry
  /schemas
  /testing

/tests
  /contract
  /unit
  /integration
  /evals

/scripts
  validate_schemas.py
  validate_prompts.py
  generate_openapi.py
  generate_clients.py later

/infra
  /docker
  /compose
```

## Stack defaults

```text
Backend language: Python 3.12+
Agent API: FastAPI
Validation: Pydantic
Database: Postgres
Migrations: Alembic
Tests: pytest
Schema validation: jsonschema or check-jsonschema
Async jobs: Redis/worker later, not required for M0-M2
Frontend: OpenWebUI first, custom TypeScript/Next.js Control Center later
TypeScript package manager: pnpm when added
Python package manager: uv preferred, pip acceptable
Local development: Docker Compose
API contracts: OpenAPI + JSON Schema
Vector search: pgvector later, not required for M0-M2
```

## API boundary rule

All clients must enter through the Agent Gateway / API Boundary.

Allowed clients:

```text
OpenWebUI chat shell
TypeScript Control Center
CLI/dev scripts
future mobile app
future browser extension
scheduled workers
```

The API boundary must enforce:

```text
Execution Contract creation or lookup
Context Pack assembly rules
Consent Ledger checks
Tool Broker path for actions
Event Ledger logging
Model Router policy
Cost policy
redaction policy
receipt generation
```

## OpenWebUI bypass prevention

OpenWebUI must not be allowed to directly run high-trust tools or write durable state. If OpenWebUI uses functions, pipelines, or tools, those capabilities should call Agent Core APIs, not raw file/database/external systems.

Forbidden bypasses:

```text
OpenWebUI Function writes memory directly
OpenWebUI Function sends external email directly
OpenWebUI Function modifies canonical files directly
OpenWebUI Function executes shell commands directly for production workflows
OpenWebUI Function bypasses Consent Ledger or Tool Broker
```

Allowed pattern:

```text
OpenWebUI → Agent Gateway → Execution Contract → Tool Broker → Tool → Event Ledger → Receipt
```

## Build phasing

### M0

Build repository structure and foundation validation:

```text
Python package skeleton
schema validation script
prompt registry validation script
basic FastAPI health endpoint optional
Docker Compose Postgres optional but recommended
OpenWebUI docker/config folder as optional shell
TypeScript app placeholder optional, not required
```

### M1–M2

Build the kernel and ledger:

```text
Execution Contract models
Context Pack models
Event Ledger events
receipts
redaction helpers
contract tests
```

### M3–M4

Add permissioned actions and durable context:

```text
Consent Ledger
Tool Broker
Memory Service
File Manager
Postgres persistence
```

### M5–M6

Add the minimal vertical slice and Foundation Gate:

```text
Orchestrator minimal run
spec generation flow
mock model routing
mock/memory file writes
contract tests
shadow replay
Foundation Gate decision
```

### After Foundation Gate

Only then build:

```text
Web Research V1
Code Workspace V1
Scanner Framework
Proactive Intelligence
Companion Proactivity
Skill Factory
Self-Improving Coding Framework
Autopilot Workflows
```

## Contract tests required

```text
OpenWebUI cannot bypass Tool Broker.
TypeScript client cannot mutate durable state directly.
All mutating API routes produce Event Ledger entries.
All tool calls require a valid Execution Contract.
Sensitive data routes respect Consent Ledger and privacy model routing.
Receipts can be produced for UI-triggered runs.
```

## Acceptance criteria

This stack decision is accepted when:

```text
The repo layout reflects the architecture.
Agent Core is recognized as the durable brain.
OpenWebUI is documented as an optional chat shell only.
TypeScript Control Center is planned as the user control layer.
Foundation Gate includes API boundary and bypass-prevention checks.
ADRs exist for the stack decisions.
M0 implementation issues reflect these choices.
```
