Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent v0.5.2 — Import Readiness Guide

Status: Pre-coding bundle with scalable stack and UI strategy incorporated.

## What this bundle is

This bundle is a canonical planning and implementation-prep package. It contains:

```text
canonical architecture docs
ADRs
JSON schemas
foundation evals
Kanban/roadmap docs
foundation implementation plan
contract test matrix
prompt pack
issue seed list
repo import checklist
scalable stack and UI strategy
```

It is ready to import as documentation, prompts, schemas, and planning artifacts.

## What this bundle is not

This bundle is not yet a runnable application. It does not include completed application source code, database migrations, provider secrets, real integrations, or production CI.

Those should be created during M0.

## Version rule

v0.5.2 is the active pre-coding baseline. Use:

```text
ultimate_ai_agent_master_plan_v0_5_2.md
docs/canonical/38_scalable_stack_and_ui_strategy.md
docs/implementation/foundation_gate_implementation_plan_v0_5_2.md
docs/prompts/prompt_registry_v0_5_2.json
```

## Recommended initial repo tree

```text
/apps
  /control-center
  /openwebui
/services
  /agent-core
  /workers
  /tool-servers
/packages
  /schemas
  /ts-client
  /python-client
/docs
/tests
/scripts
/infra
```

## First commit

Import docs, schemas, prompts, and planning files only.

Suggested commit:

```text
docs: import ultimate ai agent foundation v0.5.2
```

## Second commit

Add M0 skeleton:

```text
Python Agent Core package
schema validation script
prompt validation script
basic FastAPI app or health placeholder
Docker Compose scaffold
.env.example
CI validation workflow
```

## Foundation-first rule

Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, or external high-autonomy execution before these foundation services work:

```text
Execution Contract
Context Pack
Event Ledger
Consent Ledger
Tool Broker
Model Router
Cost Governor minimal integration
Memory Service
File Manager
Agent API Boundary
Rollback primitives
Contract tests
Shadow replay harness
```

## UI rule

OpenWebUI may be used early as a chat shell. It must not own memory, consent, event logs, files, tool permissions, scanners, self-improvement, or model routing.
