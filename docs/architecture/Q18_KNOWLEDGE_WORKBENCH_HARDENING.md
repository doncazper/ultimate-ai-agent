# Q18 Knowledge Workbench Hardening

Status: implemented local core and CLI contract. No model, provider, connector,
web, training, or automatic Chat authority is granted.

Q18 hardens the Q03 Knowledge Dump baseline into an operator-reviewable local
library. It adds durable lifecycle, rights, OCR-review, removal, cited-context,
and storage-posture truth without changing the Python Agent Core boundary.

## Implemented contract

- Every document has an `active` or `archived` lifecycle state and a rights
  state of `current`, `review_required`, or `revoked`.
- Native text is marked `not_required` for OCR review. Operator-supplied OCR is
  either `pending_review` or `reviewed`; reviewed OCR requires a bounded
  evidence ref.
- Legacy rows without extraction provenance are migrated as
  `legacy_unclassified` with rights and OCR review required. They remain
  ineligible for search and context until an exact-approved governance update
  classifies them as native text or operator-supplied OCR.
- Search and context preparation admit only active documents with current
  rights. Native text must have the native OCR posture; operator-supplied OCR
  must have a reviewed state and evidence ref.
- Governance changes are exact-scoped, optimistic-revision-bound,
  approval-required, idempotent, audited, and content-free in plans and
  receipts.
- Exact removal binds the current document and chunk revision, retention
  decision, external-backup disposition, counts, approval, and idempotency
  key. SQLite secure-delete is enabled for store connections; removal deletes
  the document, chunks, and lexical-index rows atomically while retaining a
  redacted tombstone and audit receipt.
- Removed content cannot be silently resurrected with the same bytes or ingest
  key. A changed source revision and a new reviewed ingest are required.
- `prepare-selected-context` accepts an exact ordered set of up to 32 chunk
  refs. It fails closed if any chunk is missing, archived, rights-ineligible,
  OCR-pending, or over the character budget. Every included byte remains bound
  to a `KnowledgeCitation`.
- `encryption-posture` reports owner-only permission checks and the current
  plaintext-at-rest limitation. It does not infer or claim FileVault, volume,
  application-level, or Keychain encryption.

## Local workflow

Ingest native text as before, or explicitly identify operator-supplied OCR:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  plan-ingest source.txt \
  --title "Reviewed source" \
  --rights-basis operator_authored \
  --rights-evidence-ref rights-evidence-ref:reviewed-source \
  --idempotency-key knowledge-ingest-reviewed-source \
  --extraction-method operator_supplied_ocr \
  --ocr-review-status pending_review
```

Review or archive one exact document. The first invocation prints the current
content-free plan; repeat it with the emitted exact scope ref:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py govern \
  knowledge-document-ref:sha256:replace \
  --lifecycle-state active \
  --rights-status current \
  --rights-evidence-ref rights-evidence-ref:reviewed-source \
  --extraction-method operator_supplied_ocr \
  --ocr-review-status reviewed \
  --ocr-review-evidence-ref ocr-evidence-ref:operator-reviewed \
  --idempotency-key knowledge-governance-reviewed-source
```

Prepare an exact cited pack or inspect storage posture:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  prepare-selected-context \
  --chunk-ref knowledge-chunk-ref:sha256:replace \
  --max-characters 8000
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py encryption-posture
```

Permanent removal requires reviewed retention and backup-disposition refs plus
the printed exact scope:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py remove \
  knowledge-document-ref:sha256:replace \
  --retention-decision-ref retention-decision-ref:reviewed-remove \
  --backup-disposition-ref backup-disposition-ref:reviewed-none \
  --idempotency-key knowledge-removal-reviewed-source
```

## Recovery and limits

Removal has no automatic restore path. Recovery requires an operator-managed
external backup and a separately reviewed ingest of a new source revision.
The receipt says this explicitly; it never implies rollback that the product
cannot perform.

SQLite source chunks remain plaintext inside an owner-only local database.
The operator must place the store on an operator-controlled encrypted volume.
Application-level encryption and Keychain-bound keys remain missing, not
silently implemented.

PDF parsing, image extraction, automatic OCR, embeddings, semantic retrieval,
automatic Chat injection, model calls, training-corpus export, diagnosis,
prescribing, network acquisition, connector sync, and production authority
remain blocked. Context is untrusted cited data and cannot authorize action.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_knowledge_dump.py \
  tests/test_knowledge_workbench_hardening.py \
  tests/test_knowledge_workbench_verifier.py
PYTHONPATH=src .venv/bin/python scripts/verify_queue_v2_q18_knowledge_workbench.py
```
