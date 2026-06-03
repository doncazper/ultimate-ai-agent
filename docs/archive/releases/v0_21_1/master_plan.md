Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.21.1

Status: Historical master plan for v0.21.1.

v0.21.1 hardens M17 Evidence/File/Memory Viewer safety. It is a frontend/test/verifier/docs/Foundation Gate patch only.

Implemented scope:

- alternate safe mock evidence, file ref, and memory ref entries for `/evidence`, `/files`, and `/memory`.
- accessible selected-card state for evidence, file ref, and memory summary cards.
- frontend test coverage for selecting alternate M17 metadata while staying read-only and redacted summary-only.
- static frontend verifier markers for alternate safe mock refs and selected-state reviewability.
- Foundation Gate criterion `m17_evidence_file_memory_viewer_hardening_safe`.
- v0.21.1 release docs and browser-smoke review guidance.

Architecture boundary:

- Python Agent Core remains the brain.
- Evidence, file, and memory views are inspection surfaces only.
- Memory is recall, not authority.
- Canonical files and governed source systems outrank memory.
- CCC Web displays safe refs and redacted summaries only.
- v0.21.1 adds no backend API routes and keeps OpenAPI path count unchanged at `74`.

Not implemented in v0.21.1:

- M18 Local Runtime Status + Manual Smoke Control Surface.
- backend API routes or backend viewer routes.
- file mutation, file browsing, or raw file display.
- memory mutation, memory provider implementation, embeddings, vector DB, pgvector, learn/forget/edit/delete controls, or raw memory display.
- raw evidence payload display.
- approval execution or approval grant/reject mutation.
- runtime execution or model/provider calls.
- remote execution or remote worker dispatch.
- mobile app, sensor API, OS permission integration, or native CCC implementation.
- plugin enablement, Chrome authenticated profile control, Computer Use automation, native build workflow, scanner runtime, Skill Factory, self-improvement, auth, credentials, cookies, analytics, SaaS SDKs, production persistence, or external action.
