# ADR-0056: Shared Local Application Data Platform Direction

Status: Direction accepted; dependency and implementation selection deferred to
ECO-001.

## Decision

ECO-001 must evaluate a common local application-data platform with
module-owned schemas, explicit migrations, referential integrity, versioned
projections, a unit of work, workspace/sensitivity metadata, search rebuild,
backup/restore, archive/delete, and a distinct redacted governance plane.

SQLite is the architectural baseline because UAA already uses local SQLite,
but ECO-000 does not select an encryption package, key backend, ORM, migration
framework, or search extension.

## Required proof before selection

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
