# ADR-0058: Private Data Plane And Redacted Governance Plane

Status: Accepted boundary; private persistence implementation is ECO-001 work.

## Decision

Private product values—calendar details, task text, CRM notes, source/message
content, meeting content, lists, and household data—belong only in the future
encrypted application-data plane. The governance/evidence plane stores safe
refs, hashes, bounded redacted summaries, decisions, receipts, policy outcomes,
and recovery posture.

Logs, metrics, traces, crash reports, screenshots, CLI output, fixtures,
Evidence, and support exports must not contain raw private values. Search
indexes inherit the source workspace, privacy, retention, deletion, and key
scope. Private Relationships and Dating default to exclusion from model use,
transcripts, enrichment, wallboards, shared search, and export.

## Consequences

Evidence proves what happened without becoming a second private-data store.
Screenshots and visual tests use synthetic data only. Unlock failure, integrity
failure, unsupported schema, or uncertain scope fails closed.

## Rejected

Redaction-after-logging, plaintext indexes, raw receipts, and treating a local
machine as sufficient privacy control were rejected.
