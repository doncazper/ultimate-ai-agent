# ADR-0009: Use a Project File Manager

Status: Accepted; expanded in v0.4.9

## Decision

Use a File Manager as the only production pathway for canonical files, specs, ADRs, schemas, prompts, evals, code artifacts, generated artifacts, and indexed user files.

## Rationale

Canonical files are the source of truth. They require atomic writes, diffs, versioning, indexing, rollback, and Event Ledger integration.
