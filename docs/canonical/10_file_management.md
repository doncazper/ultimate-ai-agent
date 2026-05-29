# 10 — File Management

Status: Foundation specification, v0.4.9  
Owner: File Manager / Canonical File Manager  
Layer: Layer 1 Truth and Layer 2 Tools  
Blocking: Required before Spec SDLC implementation, self-improving code, Skill Factory, and canonical project updates.

## Purpose

The File Manager controls project workspaces, canonical files, feature specs, ADRs, schemas, prompts, evals, code artifacts, generated outputs, and source-linked file indexing.

The agent must be able to create and update files, but never casually overwrite truth.

## Core rule

> Important files are changed through proposed diffs, logged operations, and rollback-ready writes.

## File classes

```text
canonical
feature_spec
ADR
schema
prompt
eval
source_code
config
artifact
uploaded_user_file
research_source
trace_export
skill_package
```

## Authority levels

| Class | Authority | Write policy |
|---|---|---|
| canonical | highest project truth | diff + policy check; approval for major changes |
| ADR | architecture decision | append/create; supersede rather than delete |
| schema | contract source | versioned; contract tests required |
| eval | quality gate | versioned; cannot be silently weakened |
| prompt | behavior control | versioned; regression eval required |
| source_code | implementation | branch/patch/test flow |
| artifact | generated output | can be created freely if within scope |
| uploaded_user_file | user source material | read-only unless explicit permission |

## File operation lifecycle

```text
request
  -> authorize
  -> read current state
  -> propose diff
  -> validate
  -> approval if needed
  -> apply atomically
  -> index/update references
  -> log event
  -> attach rollback metadata
```

## File Manager API

```text
file.read(path, scope)
file.search(query, filters)
file.create(path, content, metadata)
file.proposePatch(path, patch, reason)
file.applyPatch(patch_id)
file.writeAtomic(path, content, policy)
file.move(old_path, new_path)
file.delete(path, policy)
file.index(path)
file.getVersion(path, version)
file.rollback(operation_id)
file.export(paths)
```

## Canonical file policy

Canonical files may be updated when:

```text
The Execution Contract says canonical update is in scope.
The change matches current user instruction or approved decision.
The diff is generated and logged.
The changed file remains internally consistent.
Related ADR/spec/schema/eval updates are identified.
Major architecture changes require ADR update.
```

## Patch format

Patch proposals should include:

```text
patch_id
file_path
operation_type
reason
before_hash
after_hash
diff
related_contract_id
related_event_id
risk_level
approval_required
rollback_plan
```

## Atomicity and locking

Writes should be atomic and guarded against concurrent edits.

```text
read current file + hash
propose patch against hash
apply only if hash matches
otherwise create conflict event
```

## File indexing

The File Manager should index:

```text
path
file class
authority level
project/workspace
hash
version
summary
chunks
embeddings, optional
linked memories
linked events
linked specs/ADRs
```

## Canonical precedence and memory

When a canonical file changes:

```text
Event Ledger logs change.
Memory Curator receives candidate update.
Related memory may be written/superseded with source_ref pointing to file.
Context Pack Builder should prefer updated canonical file over old memory.
```

## Delete policy

Deletion of important files requires:

```text
explicit scope
approval if canonical/source/prompt/schema/eval/code
archival or tombstone where appropriate
rollback plan
memory/index cleanup
Event Ledger record
```

## MVP implementation notes

Start with:

```text
workspace root abstraction
file manifest table
atomic read/write
patch proposal and apply
canonical/spec/ADR generators
simple version history
file indexer for markdown/json/code
Event Ledger integration
rollback for file writes
contract tests
```

Do not build cloud-drive sync, browser extensions, or team collaboration before local/workspace file primitives are stable.
