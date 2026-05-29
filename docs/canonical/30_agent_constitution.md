# Agent Constitution

Status: Draft canonical module for Ultimate AI Agent v0.4.

## Purpose

System-wide behavioral rules for user agency, proactivity, approval, untrusted content, data minimization, and self-improvement.

## Core Principle

This module exists to make the Ultimate AI Agent more trustworthy, inspectable, evolvable, and safe to use every day.

## Responsibilities

- Define the module's role in the layered brain architecture.
- Declare public interfaces and dependencies.
- Define data owned or touched by the module.
- Define permissions and risk levels.
- Define required logs, evals, and rollback behavior.
- Define user-facing controls where applicable.

## Required Interfaces

To be completed during M0/M26 foundation work:

```text
public_api:
  - TBD
schemas:
  - TBD
events:
  - TBD
evals:
  - TBD
rollback:
  - TBD
```

## Build Notes

This canonical module was added in v0.4 because the project is becoming broad enough that user control, consent, observability, rollback, security, costs, interoperability, and stable layering must be designed before high-autonomy modules are built.

## Acceptance Criteria

- The module has a clear owner and contract.
- The module's data model is defined.
- The module's risk boundaries are defined.
- The module has at least one eval or contract test.
- The module is represented in the Capability Registry.
- The module's behavior is visible through the Event Ledger where relevant.
