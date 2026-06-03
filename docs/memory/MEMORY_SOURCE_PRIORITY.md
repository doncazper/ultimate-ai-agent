# Memory Source Priority

M24 uses a safe source priority model inspired by source hierarchy ideas, but with an important inversion: memory is never ground truth.

Priority order:

- canonical source.
- evidence manifest.
- receipt.
- Event Ledger.
- user-reviewed source.
- source-linked memory.
- unreviewed memory.
- blocked.

Trust score and confidence score are advisory metadata only. They do not grant authority. Memory is recall, not authority. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

M25 is now implemented/released for deterministic truth source routing and
evidence claim checking over provided refs only. It keeps memory as recall, not
authority, and does not turn memory into verified truth.
