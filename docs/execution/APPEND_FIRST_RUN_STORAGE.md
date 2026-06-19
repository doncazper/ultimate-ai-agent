# Append-First Run Storage

Status: active UAA-P1-025 implementation with UAA-P1-029 replay-safe receipt hashing

UAA-P1-025 adds local append-first storage for durable run records and receipt
summaries. It is a persistence layer for already-reviewed run truth only. It
does not add execution, shell or subprocess behavior, browser or network
automation, connector writes, plugin runtime import, mobile control, model or
provider authority, background workers, public distribution, or production
runtime authority.

## Storage Model

The storage file is JSONL. Each committed line is a `DurableRunStorageEntry`
with:

- schema version
- entry kind: `run_record` or `receipt`
- run id
- idempotency key
- audit ref
- receipt ref
- receipt hash schema version, for receipt entries only
- receipt hash ref, for receipt entries only
- replay validation ref, for receipt entries only
- rollback ref
- safe summary
- safe evidence refs
- previous entry hash ref
- entry hash ref

Run-record entries store a checksum-backed `DurableRunSnapshot`. Receipt entries
store redacted receipt summaries only, plus replay-safe hash refs over those
redacted summaries. The local file location is supplied by the caller and is
not copied into durable entries.

## Append And Atomicity

Each mutation builds the next logical append in memory, writes the full JSONL
sequence to a temporary sibling file, flushes and fsyncs it, then replaces the
target atomically. The in-memory index is updated only after replacement
succeeds. If replacement fails, the prior committed file and in-memory view
remain unchanged and the temporary file is removed.

This is append-first at the contract level: records only move forward through
new entries. Existing committed entries are never edited as run truth.

## Idempotency And Audit Links

Every appended run or receipt entry requires an idempotency key, audit ref,
receipt ref, rollback ref, and safe summary. Duplicate idempotency keys for the
same run are denied before persistence. Audit, receipt, and rollback refs stay
attached to each entry so replay and review can point at stable safe refs.

Receipt entries also carry `receipt_hash_ref` and `replay_validation_ref`.
`receipt_hash_ref` is built from canonical redacted receipt-summary data under
the `durable_receipt_hash.v1` schema. `replay_validation_ref` binds run ref,
receipt ref, and receipt hash ref so later replay checks can validate the same
redacted receipt without exposing private runtime content.

## Corruption Detection

Load rejects unsafe or corrupt storage when any of these checks fail:

- JSONL parse or schema validation
- durable run snapshot hash validation
- per-entry hash validation
- previous-entry hash-chain validation
- receipt hash validation for receipt entries
- replay validation ref binding for receipt entries
- duplicate entry id or duplicate per-run idempotency key on load
- unsafe receipt-summary language or unsafe values
- receipt-summary keys shaped like private-data carriers

Failures return safe error codes such as
`DURABLE_RUN_STORAGE_ENTRY_HASH_MISMATCH` and do not silently recover.

## Recovery Semantics

Reopening the storage rebuilds in-memory indexes from committed entries only.
`latest_run_record(run_id)` restores the newest durable run snapshot for that
run. Receipt summaries can be listed by run for operator review.
`validate_receipt_replay(run_id, receipt_ref)` recomputes the redacted summary
hash and returns the validated receipt entry or a safe corruption error.

UAA-P1-027 binds task decomposition to durable run records, and UAA-P1-028
defines the backup minimum set plus offline restore plan. UAA-P1-029 adds
replay-safe receipt hashing for mutating local paths. Live restore, automatic
retry, backup rotation, migration, and autonomous run continuation remain
scoped to later items. UAA-P1-025 through UAA-P1-029 prove local storage truth,
not autonomous run continuation.

## Verification

Required verification lanes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_ledger_append_only.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_atomic_writes.py
```
