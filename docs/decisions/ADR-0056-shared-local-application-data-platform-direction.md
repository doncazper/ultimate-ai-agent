# ADR-0056: Shared Local Application Data Platform Direction

Status: Accepted for the bounded ECO-001 foundation; production key backend and
application cutovers remain deferred.

## Decision

ECO-001 must evaluate a common local application-data platform with
module-owned schemas, explicit migrations, referential integrity, versioned
projections, a unit of work, workspace/sensitivity metadata, search rebuild,
backup/restore, archive/delete, and a distinct redacted governance plane.

SQLite remains the architectural baseline. ECO-001 selects application-layer
AES-GCM envelopes, injected keys, and workspace-keyed blind indexes for the
shared primitive. Exact writes validate existing `LocalApprovalAuthority`
grants before mutation; replay equality material is encrypted and visible
fingerprints are keyed. Deleted record refs are tombstoned, key cleanup is
retry-safe and reader-coordinated, schema initialization is atomic, and
backup/restore runs the same complete receipt/data integrity boundary with
bounded, trusted-ref, atomic no-replace publication. It adds no ORM or search
extension. The production macOS key and destination-path backends remain
unselected; the included in-memory backends are test-only.

The accepted implementation and its bounded non-goals are recorded in
`docs/architecture/ECO_001_SHARED_LOCAL_DATA_FOUNDATION.md`.

## Proof required before production or application cutover

- macOS-first key lifecycle: create, unlock, rotate, revoke, recover, and lose.
- Encryption of database, WAL, journal, temporary files, indexes, and backups.
- Crash-consistent local transactions and interrupted-migration recovery.
- Workspace isolation and deletion/export correctness.
- Small/medium/large dataset performance and memory measurements.
- Packaging, license, maintenance, and restore compatibility evidence.

## Alternatives retained

SQLCipher, application-layer field encryption over SQLite, and an encrypted
container around SQLite remain candidates. Plaintext SQLite for private values,
environment-variable keys, and an unbounded JSON store per app are rejected.
