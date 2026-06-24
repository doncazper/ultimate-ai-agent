# FCC-MEM-001 Memory Workbench V1

Goal: build a unified backend read model for Memory Review.

Scope:
- Combine pending candidates, accepted/corrected/rejected receipts, L1/L2/L3
  projections, context-pack proposals, and quality states.
- Add clear groups: `needs_review`, `conflict`, `duplicate`, `stale`,
  `missing_evidence`, `reviewed`, `rejected`.
- Expose a read-only route such as `GET /control-center/memory/workbench`.
- Add API manifest/OpenAPI coverage and frontend types.

Boundaries:
- The Workbench is a read model, not authority.
- No React-owned memory truth.
- No semantic search, embeddings, vector DB, context injection, delete/export
  execution, or production authority.

Verification:
- Focused backend tests for grouping and route payload.
- OpenAPI/API manifest checks.
- Frontend safety verifier after UI binding.
