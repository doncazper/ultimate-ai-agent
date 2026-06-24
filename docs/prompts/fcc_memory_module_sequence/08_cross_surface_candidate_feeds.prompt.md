# Cross-Surface Candidate Feeds

Goal: make existing surfaces feed real candidate refs into Memory Review.

Surfaces:
- Today.
- Chat receipts.
- Plans.
- Actions.
- Evidence.
- Local coding summaries.
- External assistant review summaries.

Requirements:
- Candidate refs must be backend-owned and safe-ref only.
- Source payloads remain redacted/ref-only.
- UI and docs must not imply automatic memory truth.

Verification:
- Tests prove source surfaces expose candidate refs without raw payloads.
- Evidence Timeline and Workbench show provenance.
