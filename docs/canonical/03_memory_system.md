# 03 — Memory System

Status: Foundation specification, v0.4.9  
Owner: Memory Service / Memory Curator  
Layer: Layer 1 Truth, Memory, and Data Ownership  
Blocking: Required before companion learning, proactive intelligence, scanners, Skill Factory, and self-improving code can store durable learning.

## Purpose

The Memory System gives the Ultimate AI Agent continuity without turning chat history into uncontrolled truth.

Memory is:

```text
structured
scoped
source-backed
permissioned
versioned
retrievable
supersedable
deletable
```

Memory is not the source of truth when canonical files disagree.

## Core rule

> Memory helps the agent recall and personalize; canonical files define official project truth.

## Source of truth

Use Postgres as the canonical memory database for MVP, with optional pgvector/full-text indexing. Do not start with multiple SQL databases.

## Memory lifecycle

```text
Retain
  extract candidate memories from events, files, tool results, user statements

Recall
  retrieve relevant, scoped, permissioned memories into Context Packs

Reflect
  consolidate duplicates, update summaries, resolve conflicts, supersede stale memories

Review/Delete
  let user inspect, edit, export, pause, or delete memory
```

## Memory types

```text
user_preference
relationship_memory
project_decision
project_constraint
project_fact
open_question
artifact_summary
task_summary
workflow_playbook
skill_lesson
agent_experience
belief_or_inference
source_watchlist
notification_preference
```

Inferences must be clearly marked and lower-confidence than explicit user-confirmed memory.

## Required memory fields

```text
memory_id
workspace_id
user_id
project_id, optional
entity_id, optional
type
scope
content
normalized_content
source_event_id
source_ref
confidence
trust_score
sensitivity
status
supersedes_id
valid_from
valid_to
observed_at
expires_at
tags
metadata
created_at
updated_at
schema_version
```

## Memory scopes

```text
global_user
workspace
project
relationship
task
local_private
scanner_source
```

Scopes must be enforced by the Consent Ledger and Context Pack Builder.

## Memory API

The Memory Service should expose:

```text
memory.retain(event_ref, candidates)
memory.write(write_request)
memory.search(query, scopes, filters)
memory.recall(contract_id, context_pack_request)
memory.update(memory_id, patch)
memory.supersede(old_memory_id, new_memory_id, reason)
memory.delete(memory_id, policy)
memory.reflect(scope)
memory.export(scope)
memory.pause(scope)
```

Agents do not write directly to the database.

## Retain rules

Save memory only if it is:

```text
durable
useful later
specific to the user/project/entity
source-backed
allowed by consent
not already represented or can supersede an older memory
```

Do not save:

```text
random temporary details
sensitive personal details without clear purpose/permission
raw scanner/email/message content by default
unverified external claims as facts
current emotional state unless explicitly useful and permitted
```

## Recall rules

Recall must respect:

```text
Execution Contract
Context Pack scope
Consent Ledger
canonical precedence
sensitivity
recency
confidence/trust
status active vs superseded/deleted
```

Superseded, revoked, expired, or deleted memories are excluded by default.

## Conflict handling

If memory conflicts with a canonical file:

```text
canonical wins
conflict is logged
memory may be marked stale/superseded
user may be asked if current instruction indicates a canonical change
```

If memories conflict with each other:

```text
explicit user-confirmed > tool-confirmed > recent approved decision > repeated inferred pattern > old inferred pattern
```

## Relationship memory

Companion-style learning requires careful relationship memory:

```text
preferences
boundaries
communication style
trusted people
recurring routines
important projects
notification preferences
```

It must never become uncontrolled personal surveillance. Relationship memory should be inspectable and deletable.

## Scanner-derived memory

Scanner outputs are signals, not facts. They may create:

```text
source_watchlist memories
notification preference updates
curated item summaries
research leads
```

They should not create durable facts until verified.

## Event Ledger integration

Every memory mutation must log:

```text
source event
memory id
scope
type
confidence
sensitivity
old/new values for updates
supersession links
consent basis
```

## MVP implementation notes

Start with:

```text
memories table
memory_versions table
memory_embeddings table, optional
memory_sources table
memory_edges table, minimal
Memory Service API
Memory Curator extraction prompt/schema
recall endpoint for Context Pack Builder
supersession support
user inspect/delete/export primitives
contract tests
```

Defer advanced graph memory, local cache, trust decay, and complex reflection until the Foundation Gate passes.
