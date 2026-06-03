# 03 — Memory System

Status: Foundation specification, updated for v0.28.0 / M24
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

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

## Core rule

> Memory helps the agent recall and personalize; canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources define stronger project truth than memory.

## Source of truth

M24 adds a governed `MemoryProvider` abstraction and local-only memory store foundation. M24 uses in-memory/dev storage and optional explicit-path Python stdlib SQLite only. It does not add production persistence, cloud memory providers, vector DB, embeddings, semantic search, RAG ingestion, context injection, broad filesystem scanning, backend mutation routes, or dependencies.

## Memory lifecycle

```text
Retain
  accept explicit reviewed memory record contracts only

Recall
  return redacted summary-only recall records

Reflect
  future review metadata only in M24

Review/Delete
  let user inspect, edit, export, pause, or delete memory
```

M24 has no automatic writes, model-output writes, local LLM output writes, OpenWebUI chat memory writes, Control Center memory mutation, mobile capture writes, tool output writes, raw session history storage, post-LLM learning, session-end learning, automatic extraction, auto-curated wiki, cron job, or background worker.

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

In M24, model output, local LLM output, OpenWebUI chat content, mobile capture, and tool output are not valid memory write sources. Future support requires dedicated reviewed milestones.

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
## v0.5.3 retrieval stack decision

Memory V1 uses Postgres as the canonical memory store with pgvector-ready semantic indexing, Postgres full-text search, structured filters, source-linked records, and reranking. The detailed retrieval policy is now defined in `docs/canonical/41_memory_retrieval_v1.md`.

Memory retrieval must apply scope, consent, sensitivity, supersession, freshness, source authority, and poisoning checks before memories enter a Context Pack.
