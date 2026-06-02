# Design Artifact Governance

Status: Active design governance for v0.18.2. Documentation only.

Design artifacts include screenshots, mockups, design exports, videos, visual test captures, browser smoke screenshots, visual regression outputs, and design notes.

Rules:

- do not commit screenshots with secrets.
- do not commit generated browser artifacts unless explicitly curated and reviewed.
- no private user data.
- no credentials.
- no production data.
- no browser authenticated profile capture.
- no prompts, memory contents, file contents, sensitive receipts, private hostnames, private IPs, tokens, keys, or key material.
- local-only visual smoke reports may be textual.
- any committed visual artifact requires review.
- visual artifacts must be treated as potentially sensitive until reviewed.
- design exports from SaaS or AI UI generators are not source of truth.
- design artifacts cannot bypass redaction, verifier scripts, Foundation Gate, or human review.
