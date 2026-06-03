Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent v0.5.1 — Import Readiness Guide

Status: Pre-coding readiness bundle  
Purpose: Import the current foundation into a repository without accidentally starting advanced modules too early.

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
```

It is ready to import as documentation, prompts, schemas, and planning artifacts.

## What this bundle is not

This bundle is not yet a runnable application. It does not include:

```text
application source code
Docker Compose
Postgres migrations
package manager files
CI workflow files
real model provider configuration
real tool integrations
```

Those should be created in M0 after importing this bundle.

## Import recommendation

Create a new repository and import the bundle at the repo root.

Recommended initial tree:

```text
/README.md
/docs
  /canonical
  /decisions
  /definitions
  /evals
  /implementation
  /kanban
  /milestones
  /operating
  /prompts
  /registry
  /reviews
  /schemas
  /testing
  /issues
/src
/tests
/scripts
```

For the first commit, include only docs, schemas, prompts, and planning files. Add code in the second commit.

## Version rule

v0.5.1 is the active pre-coding baseline. Older master plans may be kept as history, but implementation should use:

```text
ultimate_ai_agent_master_plan_v0_5_1.md
docs/implementation/pre_coding_readiness_v0_5_1.md
docs/prompts/prompt_registry_v0_5_1.json
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
Rollback primitives
Contract tests
Shadow replay harness
```

## Prompt status

v0.5.1 adds the initial implementation prompt pack under:

```text
docs/prompts/
```

These prompts are suitable as starting system prompts or instruction templates for the first implementation. They should be versioned, evaluated, and updated through prompt change control.
