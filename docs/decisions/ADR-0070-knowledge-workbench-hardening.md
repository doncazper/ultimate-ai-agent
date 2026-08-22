# ADR-0070: Govern Knowledge Lifecycle And Explicit Cited Context

Status: accepted for Q18.

## Decision

The local Knowledge Dump owns document lifecycle, rights posture, OCR review,
exact removal, and cited-context selection. These states are durable Python
Core and SQLite contracts, not Control Center presentation state.

Only active, rights-current sources are retrieval eligible. Native text must
retain its `not_required` OCR posture. Operator-supplied OCR remains excluded
until an exact-approved governance update records `reviewed` with a bounded
evidence ref. Operator-selected context is an ordered set of exact chunk refs;
every returned byte carries a citation and remains untrusted data.

Permanent removal is a distinct high-risk mutation. Its plan binds the current
document revision, retention decision, backup disposition, expected counts,
approval, and idempotency key. The local transaction removes source rows,
chunks, and lexical-index entries with SQLite secure-delete enabled while
preserving a content-free tombstone and audit receipt. Because Q18 implements
no restore engine, recovery posture
is stated as external-backup-only.

Encryption posture is reported rather than inferred. Owner-only filesystem
permissions are checked; source content remains plaintext at the application
layer and requires an operator-controlled encrypted volume. FileVault or other
volume encryption is not claimed without a separate verifier.

## Consequences

- Rights revocation, review-required state, archive, and pending OCR immediately
  remove a document from search and context eligibility without deleting it.
- Governance and removal reject stale revisions and conflicting idempotency
  keys.
- Removed bytes cannot be resurrected silently; a new source revision and new
  reviewed ingest are required.
- CLI inspection and mutation use the same Python Core plans, approvals,
  receipts, and safe refs.
- Plans, receipts, audit records, and tombstones omit source text and local
  paths.

## Non-goals

This decision grants no application-level encryption, Keychain integration,
automatic backup or restore, PDF parser, OCR engine, model/provider call,
automatic Chat injection, uncited context, embeddings, training authority,
network fetch, connector, diagnosis, prescribing, public beta, binary
distribution, or production authority.
