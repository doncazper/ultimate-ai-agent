# Local Knowledge Dump

Status: implemented local ingestion and lexical retrieval; explicit context
preparation implemented; automatic Chat injection and model training blocked.

The Knowledge Dump is UAA's local corpus for operator-supplied books, manuals,
papers, notes, and other robust sources. It stores extracted source chunks in a
local SQLite database, builds an FTS5 lexical index, and returns bounded source
text with document/chunk/content refs and source locators.

## Library organization

Every document is tracked with four navigational dimensions:

- source kind: `book`, `paper`, `manual`, `notes`, `article`, `dataset`, or
  `reference`
- one category slug, such as `medicine` or `business_strategy`
- an optional collection slug, such as `medical_core`
- up to 32 custom tag slugs

The inventory read model reports document, chunk, and character totals plus
facets by source kind, category, collection, tag, and file format. List results
can be filtered by any navigation dimension and sorted by newest, oldest,
title, category, or source kind. Search and context preparation accept the same
filters, allowing Chat context to be constrained to one curated shelf.

Navigation metadata can be changed later without re-ingesting or modifying the
source text. Recategorization is idempotent and requires an approval bound to
the exact document ref, prior metadata fingerprint, and proposed metadata.
Prepared updates fail closed if another accepted update changes that fingerprint
before commit.

This is retrieval-augmented context, not model-weight training. It makes a
source available for cited recall without claiming that the underlying model
has learned, verified, or internalized it.

## Supported inputs

- UTF-8 plain text and Markdown, with line locators
- HTML, with scripts and styles excluded
- EPUB, with bounded archive inspection and section locators

PDF parsing remains blocked pending a separately reviewed dependency and parser
hardening lane; scanned/image-only PDFs additionally require a future governed
OCR lane. Unsupported formats, empty sources, oversized files/archives,
secret-like content, and changing-during-read sources fail closed.

## Rights gate

Every ingest requires exactly one asserted basis:

- `operator_authored`
- `public_domain`
- `open_license`
- `licensed_for_local_retrieval`

A rights-evidence ref is mandatory. Cataloged proprietary sources, including
the registered medical textbooks and DSM material, require
`licensed_for_local_retrieval`; owning a copy or subscription is not silently
treated as corpus, embedding, or AI permission. The exact source content hash,
content-free chunk-manifest hash, title, format, size, store ref, rights
basis/evidence ref, catalog source ID, navigation metadata, and idempotency key
are bound into the approval scope. A catalog source also requires one ordered,
safe citation-locator ref for every locator requirement registered by that
source; those refs are persisted with the document and returned with every
retrieval citation. Ingest revalidates those bindings immediately
before mutation; changed chunks or plan fields fail closed.
Rights-evidence, approval, and idempotency identifiers must be bounded safe refs,
not local paths, URLs, credentials, or free-form content. Durable titles also
reject raw absolute local paths.

## Local workflow

Plan first; this reads and parses the file but does not create the store:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  plan-ingest path/to/source.epub \
  --title "Source title" \
  --rights-basis licensed_for_local_retrieval \
  --rights-evidence-ref rights-evidence-ref:replace-with-reviewed-ref \
  --idempotency-key knowledge-ingest-replace-with-unique-key \
  --source-kind book \
  --category medicine \
  --collection medical_core \
  --tag internal_medicine \
  --catalog-source-id apa_dsm_5_tr \
  --citation-locator-ref medical-locator-ref:dsm5tr-edition \
  --citation-locator-ref medical-locator-ref:dsm5tr-supplement \
  --citation-locator-ref medical-locator-ref:dsm5tr-section \
  --citation-locator-ref medical-locator-ref:dsm5tr-page
```

After reviewing the content-free plan, apply only that exact scope:
repeat every plan flag because source and navigation metadata are bound into the
approved scope.

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  ingest path/to/source.epub \
  --title "Source title" \
  --rights-basis licensed_for_local_retrieval \
  --rights-evidence-ref rights-evidence-ref:replace-with-reviewed-ref \
  --idempotency-key knowledge-ingest-replace-with-unique-key \
  --source-kind book \
  --category medicine \
  --collection medical_core \
  --tag internal_medicine \
  --catalog-source-id apa_dsm_5_tr \
  --citation-locator-ref medical-locator-ref:dsm5tr-edition \
  --citation-locator-ref medical-locator-ref:dsm5tr-supplement \
  --citation-locator-ref medical-locator-ref:dsm5tr-section \
  --citation-locator-ref medical-locator-ref:dsm5tr-page \
  --approve-exact-scope knowledge-ingest-scope-ref:replace-with-plan-ref
```

Inspect metadata, retrieve cited chunks, or prepare a bounded Chat context:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py list
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py inventory
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py audit
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  list --category medicine --collection medical_core --sort-by title
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py search "query terms"
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  prepare-context "query terms" --category medicine --tag cardiology \
  --max-characters 8000
```

Recategorize an existing document after reviewing its exact plan:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_knowledge.py \
  categorize knowledge-document-ref:replace-with-ref \
  --source-kind manual \
  --category clinical_reference \
  --collection medical_core \
  --tag cardiology \
  --idempotency-key knowledge-metadata-replace-with-unique-key \
  --approve-exact-scope knowledge-metadata-scope-ref:replace-with-plan-ref
```

The approval argument must equal the exact scope ref emitted by the immediately
preceding plan. A missing or stale value prints the current content-free plan
and refuses the mutation.

The default local store is `.uaa/knowledge_dump`, which is gitignored. `--store`
selects another local directory. Plans and receipts contain safe hashes/refs,
counts, rights metadata, and approval binding; they omit source paths and source
text. The store enforces owner-only directory and database permissions. Each
successful ingest or metadata update persists a redacted audit record in the
same transaction, including hashed requester/approver/run refs and the exact
approval, scope, receipt, idempotency, outcome, and reason refs.

An idempotency key can replay only the identical approved scope. Reusing it for
different content or metadata is rejected. Identical content submitted under a
different key is also rejected so a no-op cannot create an unrecorded key
binding. Secret-like operator refs are rejected before persistence. Search
limits are restricted to 1 through 50 results, Unicode queries follow the local
FTS tokenizer, filtered searches rank within the selected shelf, and context
packs are additionally bounded to 50,000 characters. EPUB extraction follows
the package spine rather than archive filename order.

## Chat boundary

`prepare-context` returns the selected source chunks because those chunks are
the useful knowledge payload. Each chunk is explicitly marked untrusted data,
not an instruction, and includes its citation locator. The pack also instructs
the eventual Chat composer to cite sources and disclose uncertainty/conflicts.

The current lane does not call a model or provider and does not automatically or
silently inject the pack into Chat. Connecting an operator-selected pack to the
Python Core Chat composer requires a separate exact change with UI/API/CLI
parity, token-budget enforcement, citation rendering, prompt-injection tests,
and no expansion of provider or model authority.

## Safety and current limits

- No network fetch, crawler, connector, browser, or provider SDK is used.
- No embeddings, vector database, semantic search, background indexing, model
  fine-tuning, or training corpus export is enabled.
- SQLite stores source chunks locally in plaintext. The dump must remain on an
  operator-controlled encrypted volume; application-level encryption and
  Keychain-bound keys are future hardening.
- Source content may contain incorrect, malicious, stale, or contradictory
  statements. Retrieval never grants truth, instruction, diagnosis,
  prescribing, action, approval, or production authority.
- An approved removal/rollback command and Control Center management surface are
  not implemented in this slice. Until then, operators may safe-disable the
  entire dump by moving the local store directory out of UAA's configured path;
  exact per-document lifecycle remains follow-up work.
