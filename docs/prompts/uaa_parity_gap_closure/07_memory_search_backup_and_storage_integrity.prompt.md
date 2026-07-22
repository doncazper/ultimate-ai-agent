# Phase 07: Memory, Search, Backup, And Storage Integrity

Coverage: H03, H06, O04, P03, B08, B09, B10, L11, L12, and L16.

Objective: make Memory and local product storage concurrency-safe,
provenance-preserving, searchable without an LLM, and recoverable through a
verified backup/restore lifecycle.

## Fresh Delta Gate

Re-inventory governed memory, ranked retrieval, context manifests, session
search, SQLite/file stores, migrations, backup utilities, file/path guards, and
in-flight Memory work. Extend the canonical stores; do not create a parallel
memory database or a second truth index.

## Memory Integrity Outcomes

1. Audit every durable memory mutation for transaction or atomic-replace
   behavior, lock scope, stale-version detection, crash recovery, duplicate
   decisions, provenance preservation, and deterministic conflict handling.
2. Prove corrections, rejects, merges, supersedes, and deletion/tombstone rules
   remain authoritative after concurrent writes and migrations.
3. Invalidate retrieval caches and derived indexes on every relevant mutation
   or migration. Bound every cache and document TTL/eviction semantics.
4. Preserve memory as recall, not truth or authority. No hidden automatic
   context injection is introduced.

## LLM-Free Search Outcomes

1. Add cross-session/operator search over redacted titles, bounded summaries,
   safe refs, state, dates, tags, evidence refs, and approved memory fields.
2. Support exact path/title/stem-style ranking only for safe refs; never expose
   raw local paths or index raw prompt/response bodies.
3. Provide filters, pagination/cursors, deterministic ordering, provenance,
   stale-index state, CLI/API/Control Center parity, and query benchmarks.
4. Compact reads must reduce bytes/tokens without changing evidence meaning or
   dropping provenance.

## Backup And Restore Outcomes

1. Implement local backup create, list, verify, and restore for current durable
   UAA stores using a versioned manifest, schema identity, hashes, sizes,
   timestamps, redaction/encryption posture, and source safe refs.
2. Default restore to a fresh target. In-place restore requires a separately
   approved exact mutation with pre-restore backup and rollback plan.
3. Verify before restore and fail closed on tamper, truncation, duplicate entry,
   schema mismatch, unsupported version, missing artifact, or hash mismatch.
4. Reject absolute paths, traversal, symlink/hardlink escape, archive bombs,
   special files, and entry-name collisions.
5. Account for databases, WAL/journal files, migrated sidecars, temporary files,
   backups, indexes, and retained receipts in storage budgets.

## End-To-End Acceptance

- Run concurrent memory decisions and inject controlled crash points.
- Rebuild/search the real local index and compare relevance/latency to fixtures.
- Create and verify a real backup, restore into a fresh target, launch UAA
  against it, and compare safe state hashes and critical read models.
- Tamper with one artifact and exercise traversal/symlink/archive attacks.
- Prove no raw sensitive material appears in durable reports.

Commit message:

```text
feat(storage): harden memory search backup and recovery
```
