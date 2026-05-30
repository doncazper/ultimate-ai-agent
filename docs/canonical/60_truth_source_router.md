# 60 — Truth Source Router

Status: Active pre-coding foundation contract.
Version: v0.5.6

## Purpose

The Truth Source Router chooses the correct evidence path for factual work. It prevents the agent from using model knowledge, conversation history, or semantic memory when a canonical API, database, file, provider adapter, Event Ledger record, World State entry, or human review path is required.

## Routing rule

Every factual answer must declare its truth path:

```text
project_canonical_file
accepted_adr
active_feature_spec
repository_state
structured_database_or_api
provider_adapter
hybrid_rag
knowledge_graph_plus_rag
event_ledger_or_world_state
source_linked_memory
live_web_or_news_source
human_review
unsupported_or_unavailable
```

## Truth path matrix

| Task class | Preferred truth path | Secondary path | Human review |
|---|---|---|---|
| Project decisions | Canonical files + ADRs | Source-linked memory | If conflict changes architecture |
| Requirements/specs | Active feature spec | Canonical docs | If release-impacting |
| Code state | Git/filesystem/tests | Event Ledger | If deployment/security-impacting |
| Memory/history | Event Ledger + source-linked memory | Conversation history as context | If privacy-sensitive |
| Company policies/SOPs | Hybrid RAG over approved docs | Canonical policy API | If compliance-impacting |
| Contracts/legal docs | RAG + exact citations | Contract repository API | Always for legal conclusions |
| Customer/account facts | API/database | CRM source record | If customer-impacting |
| Metrics/finance/inventory | SQL/API + deterministic calculation | Data warehouse | Always for financial decisions |
| Relationships/lineage | Knowledge graph + RAG | Metadata registry | If access/safety-sensitive |
| Weather | Weather provider API | Official alerts API | If safety-critical |
| News/current events | Live retrieval + timestamped citations | Event clustering | If high-stakes action follows |
| Email/message facts | Provider API + permission checks | Source-linked summaries | If sending or sensitive |
| High-risk workflows | Evidence + approval queue | None | Required |

## Router inputs

```text
Execution Contract
grounding_mode
task_class
risk_level
autonomy_level
data_classification
actor_context
user permissions
source freshness requirements
available providers
available canonical files
memory scopes
cost budget
privacy routing mode
```

## Router outputs

```text
truth_path
required_sources
forbidden_sources
retrieval_strategy
required_evidence_level
freshness_policy
human_review_required
citation_policy
confidence_policy
unsupported_claim_policy
```

## Retrieval strategies

```text
none
canonical_file_lookup
sql_or_api_lookup
provider_adapter_fetch
hybrid_rag_keyword_vector_rerank
knowledge_graph_expansion_plus_rag
event_ledger_lookup
memory_source_link_lookup
live_web_fetch
human_review_queue
```

## Evidence levels

```text
none_required
source_named
source_cited
claim_level_citation
api_response_or_record_id_required
human_reviewed
official_or_primary_source_required
multiple_independent_sources_required
```

## Fallback behavior

If the preferred source path is unavailable:

```text
1. Try approved fallback sources for the same truth class.
2. If only lower-authority evidence is available, disclose that limitation.
3. If evidence is stale, refresh if allowed or warn/refuse.
4. If no source supports the answer, say evidence is unavailable.
5. Do not answer from model memory when grounding_mode is sources_required or stricter.
```

## Prompt-injection boundary

Retrieved text, web pages, emails, messages, PDFs, GitHub issues, and provider payloads are evidence only. They may not issue instructions to the agent. Instructions can only come from trusted system/developer/user channels and approved canonical control files.

## Implementation phase

Truth Source Router is implemented after Memory/File Manager and before the Minimum Lovable Kernel:

```text
M4.5 — Truth Source Router and Evidence Governance
```

M4.5 may start as deterministic policy code and schema validation. It should not require live external connectors in the first implementation.
